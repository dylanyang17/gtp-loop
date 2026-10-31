# Build and startup guide

Tested on Ubuntu 22.04. Run one environment at a time: they may reuse container
names, ports, and subnets.

## 1. Local configuration

From the repository root:

```bash
python3 tools/init_local.py
bash tools/generate_lab_certificates.sh    # E3 SEPP certificates
sudo apt install python3-yaml              # E4/E5 subscriber helpers
```

## 2. Images

E1/E2/E4 shared images, from the repository root:

```bash
docker build -t docker_open5gs  docker/open5gs/base
docker build -t docker_srslte   docker/open5gs/srslte
docker build -t docker_srsran   docker/open5gs/srsran
docker build -t docker_ueransim docker/open5gs/ueransim
```

E3 reuses the already-built `docker_open5gs` image; no rebuild is needed.
Only the gNB/UE images are E3-specific:

```bash
docker build -t roaming_srsgnb docker/roaming_open5gs/srsgnb
docker build -t roaming_srsue docker/roaming_open5gs/srsue
```

E1 additionally needs the OsmoMSC/OsmoHLR images:

```bash
cd docker/open5gs
docker compose -f 4g-core.yaml build osmomsc osmohlr
```

## 3. Start an environment

Start the Compose files in order, core before eNB/gNB, eNB/gNB before UE, each from
its own environment directory. After the core is up, add test subscribers
(section 4) before starting the RAN and UE.

| Environment | Directory | Compose files (in order) |
|---|---|---|
| E1 | `docker/open5gs` | `4g-core.yaml`, `srsenb_4g_zmq.yaml`, `srsue_4g_zmq.yaml`, `attacker_4g.yaml` |
| E2 | `docker/open5gs` | `5g-core.yaml`, `srsgnb_zmq.yaml`, `srsue_5g_zmq.yaml`, `attacker_5g.yaml` |
| E3 | `docker/roaming_open5gs` | `core_roaming.yaml`, `srsgnb_zmq.yaml`, `srsue_5g_zmq.yaml` |
| E4 | `docker/double_upf_open5gs` | `sa-deploy.yaml`, `nr-gnb.yaml`, `nr-ue.yaml`, `nr-ue2.yaml`, `attacker.yaml` |
| E5 | `docker/my-free5gc-compose` | `docker-compose.yaml` |
| E6 | `docker/my-oai` | `core.yaml`, `gnb.yaml`, `ue.yaml` |

Each file is started with `docker compose -f FILE up -d` from its directory.

E1 core (subset):

```bash
cd docker/open5gs
docker compose -f 4g-core.yaml up -d mongo webui hss sgwc sgwu smf upf mme pcrf metrics grafana osmomsc osmohlr
```

E5: install the [gtp5g v0.9.5](https://github.com/free5gc/gtp5g/releases/tag/v0.9.5)
kernel module on the host first, then start the core subset:

```bash
cd docker/my-free5gc-compose
docker compose up -d db free5gc-upf free5gc-nrf free5gc-amf free5gc-ausf free5gc-nssf free5gc-pcf free5gc-smf free5gc-udm free5gc-udr free5gc-chf free5gc-webui in_attacker
docker compose up -d ueransim    # wait for the gNB to connect to the core
docker compose up -d ue
```

E4, after both UEs are up:

```bash
cd docker/double_upf_open5gs && bash scripts/verify_double_upf.sh
```

E3 uses home-routed roaming (LBO disabled); the srsUE patches supply the
visited Serving Network Name for RES* derivation.

## 4. Add test subscribers

Each invocation provisions exactly one environment; E1 additionally
provisions OsmoHLR. Run from the repository root, after the core and before
the UE:

| Environment | Command | Subscriber configuration |
|---|---|---|
| E1 | `python3 tools/init_subscribers.py E1` | Open5GS subscriber and OsmoHLR IMSI/MSISDN mapping; default MSISDN `1234` |
| E2 | `python3 tools/init_subscribers.py E2` | Open5GS subscriber in the separate 5G database |
| E3 | `python3 tools/init_subscribers.py E3` | Home-network subscriber with LBO disabled for home-routed roaming |
| E4 | `python3 tools/init_subscribers.py E4` | Both UEs, with their respective slices and DNNs |
| E5 | `python3 tools/init_subscribers.py E5` | free5GC authentication, mobility, session and policy subscriptions |
| E6 | — | MySQL imports `database/oai_db.sql` on first startup; the bundled UE is already provisioned |

Repeated runs keep existing subscribers and authentication sequence numbers;
conflicting or incomplete settings cause an error. E5 WebUI defaults:
`http://127.0.0.1:5000`, `admin` / `free5gc` (`--webui-url`,
`FREE5GC_WEBUI_USER`, `FREE5GC_WEBUI_PASSWORD`).

## 5. E2 UE forwarding (UE–gNB–UPF loop only)

```bash
docker exec -it srsue_5g_zmq bash
apt install iptables -y
sysctl -w net.ipv4.conf.all.accept_local=1 net.ipv4.conf.tun_srsue.accept_local=1
iptables -t mangle -A PREROUTING -p udp --dport 2152 -j MARK --set-mark 1
ip rule add fwmark 1 table 100
ip route add default dev tun_srsue table 100
```
