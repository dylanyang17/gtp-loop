# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 gtp-loop contributors.
"""Provision test subscribers after core startup and before UE startup."""

import argparse
import configparser
import copy
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENTS = {
    "E1": ("open5gs", "4g-core.yaml", "mongo"),
    "E2": ("open5gs", "5g-core.yaml", "mongo"),
    "E3": ("roaming_open5gs", "core_roaming.yaml", "hdb"),
    "E4": ("double_upf_open5gs", "sa-deploy.yaml", "mongo"),
    "E5": ("my-free5gc-compose", "docker-compose.yaml", "db"),
}


def run(command, directory, data=None):
    result = subprocess.run(command, cwd=directory, input=data, text=True,
                            encoding="utf-8", capture_output=True, timeout=20)
    if result.returncode:
        # Do not include the stdin payload, which contains subscriber keys.
        raise RuntimeError(result.stderr.strip() or "Command failed: " + command[0])
    return result.stdout.strip()


def wait_for(action, description, timeout):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return action()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            if time.monotonic() >= deadline:
                raise RuntimeError("Timed out waiting for " + description) from error
            time.sleep(1)


def checked(value, pattern, label):
    if not re.fullmatch(pattern, value):
        raise ValueError("Invalid " + label)
    return value


def read_ueransim(path, environment):
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("E4/E5 require PyYAML; on Ubuntu: sudo apt install python3-yaml") from error
    # Keep IMSIs, MNCs and hexadecimal SDs as strings, including leading zeros.
    config = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    for key in ("supi", "key", "op", "amf", "mcc", "mnc"):
        for name, value in environment.items():
            config[key] = config[key].replace(name, value)
    config["imsi"] = checked(config["supi"].removeprefix("imsi-"), r"[0-9]{15}", "IMSI")
    for key in ("key", "op"):
        config[key] = checked(config[key], r"[0-9a-fA-F]{32}", key).upper()
    config["amf"] = checked(config["amf"], r"[0-9a-fA-F]{4}", "AMF").upper()
    if config["opType"] not in ("OP", "OPC"):
        raise ValueError("Unsupported opType")
    checked(config["mcc"], r"[0-9]{3}", "MCC")
    checked(config["mnc"], r"[0-9]{2,3}", "MNC")
    if not config["imsi"].startswith(config["mcc"] + config["mnc"]):
        raise ValueError("IMSI does not match UE PLMN")
    sessions = []
    for session in config["sessions"]:
        if session["type"].upper() != "IPV4":
            raise ValueError("Only the bundled IPv4 UERANSIM sessions are supported")
        snssai = {"sst": int(session["slice"]["sst"], 0)}
        if not 0 <= snssai["sst"] <= 255:
            raise ValueError("Invalid slice SST")
        if "sd" in session["slice"]:
            sd = session["slice"]["sd"].lower().removeprefix("0x")
            snssai["sd"] = checked(sd, r"[0-9a-f]{6}", "slice SD")
        dnn = checked(session["apn"], r"[A-Za-z0-9_-]+", "DNN")
        sessions.append((snssai, dnn))
    if not sessions:
        raise ValueError("No UE sessions configured")
    config["sessions"] = sessions
    return config


def open5gs_subscriber(imsi, key, op, amf, op_type, sessions, msisdn=None, roaming=False):
    checked(imsi, r"[0-9]{15}", "IMSI")
    security = {"k": checked(key, r"[0-9a-fA-F]{32}", "key").upper(),
                "amf": checked(amf, r"[0-9a-fA-F]{4}", "AMF").upper(),
                "op": None, "opc": None}
    security["op" if op_type == "OP" else "opc"] = checked(op, r"[0-9a-fA-F]{32}", "OP/OPc").upper()
    ambr = {"downlink": {"value": 1, "unit": 3}, "uplink": {"value": 1, "unit": 3}}
    slices = []
    for snssai, dnn in sessions:
        item = next((s for s in slices if s["sst"] == snssai["sst"] and s.get("sd") == snssai.get("sd")), None)
        if item is None:
            item = dict(snssai, default_indicator=not slices, session=[])
            slices.append(item)
        session = {"name": dnn, "type": 1, "ambr": copy.deepcopy(ambr), "pcc_rule": [],
                   "qos": {"index": 9, "arp": {"priority_level": 8,
                           "pre_emption_capability": 1, "pre_emption_vulnerability": 1}}}
        if roaming:
            session["lbo_roaming_allowed"] = False
        item["session"].append(session)
    return {"imsi": imsi, "msisdn": [msisdn] if msisdn else [], "security": security,
            "slice": slices, "ambr": ambr, "schema_version": 1,
            "access_restriction_data": 32, "subscriber_status": 0,
            "network_access_mode": 0, "subscribed_rau_tau_timer": 12}


def open5gs_users(name, directory, env, msisdn):
    if name == "E4":
        users = []
        for file, number in (("ueransim-ue.yaml", "1001"), ("ueransim-ue2.yaml", "1002")):
            ue = read_ueransim(directory / "ueransim" / file, env)
            users.append(open5gs_subscriber(ue["imsi"], ue["key"], ue["op"], ue["amf"],
                                           ue["opType"], ue["sessions"], number))
        return users
    config = configparser.ConfigParser()
    file = "ue_zmq.conf" if name == "E1" else "ue_5g_zmq.conf"
    config.read(directory / ("srsue" if name == "E3" else "srslte") / file)
    nas = config["nas"]
    snssai = {"sst": int(nas.get("nssai-sst", "1"))}
    if nas.get("nssai-sd"):
        snssai["sd"] = nas["nssai-sd"].lower().removeprefix("0x")
    op_name = "UE1_OPC" if name == "E3" else "UE1_OP"
    return [open5gs_subscriber(env["UE1_IMSI"], env["UE1_KI"], env[op_name], env["UE1_AMF"],
                              "OPC", [(snssai, nas["apn"])], msisdn if name == "E1" else None,
                              roaming=name == "E3")]


class Vty:
    """Read OsmoHLR prompts and refuse unused Telnet options.

    OsmoHLR 1.9.x reprints its prompt after an idle period, and command
    output can trail an earlier stray prompt. A response that consists of
    bare prompt lines only is therefore not accepted immediately: we wait
    briefly for extra bytes and keep reading if the real output follows.
    """

    def __init__(self, host):
        self.socket = socket.create_connection((host, 4258), timeout=5)
        try:
            self.read_prompt()
        except Exception:
            self.socket.close()
            raise

    @staticmethod
    def _prompt_only(output):
        # Every non-empty line looks like a prompt ("OsmoHLR# ", "OsmoHLR> ").
        for line in output.split(b"\n"):
            line = line.strip(b"\r")
            if line and not re.fullmatch(rb"[^\r\n]*[>#] $", line):
                return False
        return True

    def _settle(self, seconds):
        # True when no further bytes arrive within the window.
        self.socket.settimeout(seconds)
        try:
            self.socket.recv(1, socket.MSG_PEEK)
            return False
        except socket.timeout:
            return True
        finally:
            self.socket.settimeout(5)

    def read_prompt(self):
        output = bytearray()
        while True:
            value = self.socket.recv(1)
            if not value:
                raise RuntimeError("OsmoHLR closed the VTY connection")
            if value == b"\xff":
                command = self.socket.recv(1)
                if command in (b"\xfb", b"\xfc", b"\xfd", b"\xfe"):
                    option = self.socket.recv(1)
                    if command in (b"\xfb", b"\xfd"):
                        self.socket.sendall(b"\xff" + (b"\xfe" if command == b"\xfb" else b"\xfc") + option)
                elif command == b"\xfa":
                    previous = b""
                    while True:
                        current = self.socket.recv(1)
                        if not current:
                            raise RuntimeError("Incomplete Telnet negotiation")
                        if previous == b"\xff" and current == b"\xf0":
                            break
                        previous = current
                continue
            output.extend(value)
            if re.search(rb"(?:^|[\r\n])[^\r\n]*[>#] $", output):
                if self._prompt_only(output) and not self._settle(2.5):
                    continue
                return output.decode("utf-8", errors="replace")

    def command(self, command):
        self.socket.sendall(command.encode("ascii") + b"\r\n")
        response = self.read_prompt()
        if re.search(r"(?im)^% (Unknown|Ambiguous|Command incomplete|Error|MSISDN invalid)", response):
            raise RuntimeError("OsmoHLR rejected command: " + command)
        return response


def provision_hlr(host, imsi, msisdn, timeout):
    vty = wait_for(lambda: Vty(host), "OsmoHLR VTY", timeout)
    try:
        vty.command("enable")
        show = vty.command("subscriber imsi " + imsi + " show")
        if "No subscriber for" in show:
            vty.command("subscriber imsi " + imsi + " create")
        else:
            match = re.search(r"MSISDN:\s*(\S+)", show)
            if not match:
                raise RuntimeError("Cannot read existing OsmoHLR subscriber")
            if match[1] not in ("none", msisdn):
                raise RuntimeError("OsmoHLR MSISDN differs; existing subscriber was preserved")
        vty.command("subscriber imsi " + imsi + " update msisdn " + msisdn)
        show = vty.command("subscriber imsi " + imsi + " show")
        if not re.search(r"MSISDN:\s*" + re.escape(msisdn) + r"\s", show):
            raise RuntimeError("OsmoHLR subscriber verification failed")
        print("OsmoHLR subscriber ready: " + imsi)
    finally:
        vty.socket.close()


def request_json(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Token"] = token
    request = urllib.request.Request(url, method=method, headers=headers,
                                     data=json.dumps(data).encode() if data is not None else None)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError("free5GC WebUI returned HTTP " + str(error.code)) from error


def free5gc_payload(ue, sample):
    payload = copy.deepcopy(sample)
    payload["ueId"], payload["plmnID"] = ue["supi"], ue["mcc"] + ue["mnc"]
    auth = payload["AuthenticationSubscription"]
    auth["permanentKey"]["permanentKeyValue"] = ue["key"]
    auth["authenticationManagementField"], auth["sequenceNumber"] = ue["amf"], "000000000000"
    auth["milenage"] = {"op": {"opValue": ue["op"] if ue["opType"] == "OP" else ""}}
    auth["opc"] = {"opcValue": ue["op"] if ue["opType"] == "OPC" else ""}
    am = payload["AccessAndMobilitySubscriptionData"]
    am["gpsis"] = [""]  # The WebUI accepts an empty MSISDN for data-only UEs.
    slices = []
    for snssai, _ in ue["sessions"]:
        if snssai not in slices:
            slices.append(snssai)
    am["nssai"] = {"defaultSingleNssais": slices, "singleNssais": slices}
    session_template = payload["SessionManagementSubscriptionData"][0]
    dnn_template = next(iter(session_template["dnnConfigurations"].values()))
    payload["SessionManagementSubscriptionData"] = []
    selection, policy = {}, {}
    for snssai in slices:
        dnns = [dnn for s, dnn in ue["sessions"] if s == snssai]
        payload["SessionManagementSubscriptionData"].append({
            "singleNssai": snssai, "dnnConfigurations": {d: copy.deepcopy(dnn_template) for d in dnns}})
        key = format(snssai["sst"], "02x") + snssai.get("sd", "")
        selection[key] = {"dnnInfos": [{"dnn": d} for d in dnns]}
        policy[key] = {"snssai": snssai, "smPolicyDnnData": {d: {"dnn": d} for d in dnns}}
    payload["SmfSelectionSubscriptionData"] = {"subscribedSnssaiInfos": selection}
    payload["SmPolicyData"] = {"smPolicySnssaiData": policy}
    return payload


def verify_free5gc(actual, expected):
    # Ignore SQN and server metadata. Check the settings needed by these UEs.
    auth = copy.deepcopy(expected["AuthenticationSubscription"])
    del auth["sequenceNumber"]
    empty_type = "milenage" if not auth["milenage"]["op"]["opValue"] else "opc"
    del auth[empty_type]

    def contains(value, wanted):
        if isinstance(wanted, dict):
            return isinstance(value, dict) and all(k in value and contains(value[k], v) for k, v in wanted.items())
        if isinstance(wanted, list):
            return isinstance(value, list) and all(any(contains(v, w) for v in value) for w in wanted)
        if isinstance(wanted, str) and re.fullmatch(r"[0-9a-fA-F]+", wanted):
            return isinstance(value, str) and value.lower() == wanted.lower()
        return value == wanted

    required = {"AuthenticationSubscription": auth}
    for field in ("AccessAndMobilitySubscriptionData", "SessionManagementSubscriptionData",
                  "SmfSelectionSubscriptionData", "SmPolicyData"):
        required[field] = expected[field]
    # Existing MSISDNs are unrelated to the data-only test.
    required["AccessAndMobilitySubscriptionData"] = copy.deepcopy(required["AccessAndMobilitySubscriptionData"])
    required["AccessAndMobilitySubscriptionData"].pop("gpsis", None)
    if not contains(actual, required):
        raise RuntimeError("free5GC subscriber differs or is incomplete; existing data was preserved")


def provision_free5gc(directory, url, timeout):
    ue = read_ueransim(directory / "config/uecfg.yaml", {})
    url = url.rstrip("/") + "/api"
    sample = wait_for(lambda: request_json(url + "/sample"), "free5GC WebUI", timeout)
    login = request_json(url + "/login", "POST", {
        "username": os.environ.get("FREE5GC_WEBUI_USER", "admin"),
        "password": os.environ.get("FREE5GC_WEBUI_PASSWORD", "free5gc")})
    token = login["access_token"]
    payload = free5gc_payload(ue, sample)
    path = url + "/subscriber/" + ue["supi"] + "/" + payload["plmnID"]
    current = request_json(path, token=token)
    # An absent subscriber is returned as a 200 response with an empty auth object.
    if not (current.get("AuthenticationSubscription") or {}).get("permanentKey"):
        # Refuse incomplete provisioning rather than replacing any existing auth data.
        existing = request_json(url + "/subscriber", token=token)
        if any(item["ueId"] == ue["supi"] for item in existing):
            raise RuntimeError("Incomplete free5GC subscriber exists; inspect it in the WebUI")
        request_json(path, "POST", payload, token)
        current = request_json(path, token=token)
    verify_free5gc(current, payload)
    print("free5GC subscriber ready: " + ue["supi"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=ENVIRONMENTS,
                        help="provision exactly this environment's subscriber(s)")
    parser.add_argument("--timeout", type=int, default=90, help="service readiness timeout in seconds")
    parser.add_argument("--msisdn", default="1234", help="E1 test subscriber phone number (default: 1234)")
    parser.add_argument("--webui-url", default="http://127.0.0.1:5000", help="E5 WebUI URL")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    checked(args.msisdn, r"[0-9]{1,15}", "MSISDN")
    folder, filename, database = ENVIRONMENTS[args.environment]
    directory = ROOT / "docker" / folder
    compose = ["docker", "compose", "-f", filename]
    config = json.loads(run(compose + ["config", "--format", "json"], directory))
    if args.environment == "E5":
        provision_free5gc(directory, args.webui_url, args.timeout)
        return
    env = config["services"][database]["environment"]
    users = open5gs_users(args.environment, directory, env, args.msisdn)
    command = compose + ["exec", "-T", database, "mongosh", "--quiet", "open5gs"]
    wait_for(lambda: run(command + ["--eval", "db.runCommand({ping:1})"], directory),
             "Open5GS MongoDB", args.timeout)
    script = (ROOT / "tools/init_open5gs_subscribers.js").read_text(encoding="utf-8")
    output = run(command + ["--file", "/dev/stdin"], directory,
                 "const subscribers = " + json.dumps(users) + ";\n" + script)
    print(output)
    if args.environment == "E1":
        provision_hlr(env["OSMOHLR_IP"], users[0]["imsi"], args.msisdn, args.timeout)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        sys.exit("Subscriber initialization failed: " + str(error))
