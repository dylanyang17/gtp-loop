# gtp-loop

Experimental environments and patches for our NDSS 2027 paper:

**Looping the Core: Exploiting GTP-U Forwarding Semantics in Cellular Networks**

## Environments

E1-E6 correspond to the deployments evaluated in the paper.

| Environment | Core / RAN | Loop instance(s) | Directory |
|---|---|---|---|
| E1: 4G EPC | Open5GS / srsRAN 4G | SGW-PGW (F1-F2) | [`docker/open5gs`](docker/open5gs/) |
| E2: 5G standalone | Open5GS / srsRAN | UPF self-loop (Single-F2); UE-gNB-UPF (F1-F2) | [`docker/open5gs`](docker/open5gs/) |
| E3: Home-routed 5G roaming | Open5GS / srsRAN | vUPF-hUPF (F1-F2) | [`docker/roaming_open5gs`](docker/roaming_open5gs/) |
| E4: Dual-UPF 5G standalone | Open5GS / UERANSIM | Dual-UPF (Multi-F2) | [`docker/double_upf_open5gs`](docker/double_upf_open5gs/) |
| E5: 5G standalone | free5GC / UERANSIM | UPF self-loop (Single-F2) | [`docker/my-free5gc-compose`](docker/my-free5gc-compose/) |
| E6: 5G standalone | OAI-CN5G / OAI gNB and UE | UPF self-loop (Single-F2) | [`docker/my-oai`](docker/my-oai/) |

## Setup

The environments were tested on Ubuntu 22.04. To run them, you will need:

- Docker Engine and Docker Compose on a Linux host with administrative access.
- Python 3.9 or newer. E4/E5 subscriber initialization also uses PyYAML
  (`sudo apt install python3-yaml` on Ubuntu).
- OpenSSL for generating SEPP certificates in E3.
- The `gtp5g` v0.9.5 kernel module for E5 (free5GC).

Prepare the local configuration files from the repository root:

```bash
python3 tools/init_local.py
```

The [setup guide](docs/SETUP.md)
provides the build commands, startup order, and subscriber initialization commands for each
environment. Run one environment at a time because they may reuse container names, ports, and subnets.

## Patches

- The Open5GS base Dockerfiles increase `OGS_MAX_PKT_LEN` from 2048 to 70000.
- The E3 srsUE patches ([lib.patch](docker/roaming_open5gs/srsue/lib.patch) and
  [srsue.patch](docker/roaming_open5gs/srsue/srsue.patch)) add a configurable
  Serving Network Name for roaming authentication.

## License

Original contributions are licensed under [BSD-2-Clause](LICENSE). The srsRAN
patches use [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt). See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream licenses and attribution.
