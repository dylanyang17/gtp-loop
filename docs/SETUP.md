# Build and startup guide

## Configuration

Prepare local `.env` files from the repository root:

```bash
python3 tools/init_local.py
```

Existing `.env` files are not overwritten.

E5 includes the public test certificates and keys from
[free5gc-compose v4.2.1](https://github.com/free5gc/free5gc-compose/tree/v4.2.1/cert).

For E3, generate the local SEPP certificates before starting the containers.
The helper calls the host's `openssl` command:

```bash
bash tools/generate_lab_certificates.sh
```

Subscriber credentials must match the selected UE configuration.
Generated `.env` files and local private keys are ignored by Git. The upstream
free5GC test certificates and keys are included explicitly.

The dual-UPF example uses `172.24.0.0/24` for its Docker bridge network.
Subscriber keys and device identifiers are public test examples.

## Add test subscribers

For E1-E5, start the selected core, then run the corresponding command below
**from the repository root before starting the UE**. The helper waits for the
database or WebUI to respond. It reads the resolved Compose environment for
Open5GS and the UE configuration files for E4/E5.

| Environment | Command | Subscriber configuration |
|---|---|---|
| E1 | `python3 tools/init_subscribers.py E1` | Open5GS subscriber and OsmoHLR IMSI/MSISDN mapping; default MSISDN `1234` |
| E2 | `python3 tools/init_subscribers.py E2` | Open5GS subscriber in the separate 5G database |
| E3 | `python3 tools/init_subscribers.py E3` | Home-network subscriber with LBO disabled for home-routed roaming |
| E4 | `python3 tools/init_subscribers.py E4` | Both UEs, with their respective slices and DNNs |
| E5 | `python3 tools/init_subscribers.py E5` | free5GC authentication, mobility, session and policy subscriptions |
| E6 | No extra command | MySQL imports `database/oai_db.sql` on its first startup; the bundled UE is already provisioned |

Install PyYAML for E4/E5 (`sudo apt install python3-yaml` on Ubuntu).
Repeated runs keep existing subscribers and authentication sequence numbers.
Conflicting or incomplete subscriber settings cause an error; inspect the
existing record before changing it. The helper does not clear any database.

E1 accesses OsmoHLR at its configured `OSMOHLR_IP`, port `4258`, from the Linux
Docker host. Use `--msisdn NUMBER` if a different test number is needed.
For E5 the default WebUI is `http://127.0.0.1:5000`, with login `admin` / `free5gc`.
Use `--webui-url URL` or the `FREE5GC_WEBUI_USER` and `FREE5GC_WEBUI_PASSWORD`
environment variables if these have changed.

User provisioning does not apply the optional E2 UE forwarding rules below.

## Compose entry points

| Paper | Scenario | Directory | Compose files (in startup order) |
|---|---|---|---|
| E1 | Open5GS 4G EPC, SGW–PGW | `docker/open5gs` | `4g-core.yaml`, `srsenb_4g_zmq.yaml`, `srsue_4g_zmq.yaml`, `attacker_4g.yaml` |
| E2 | Open5GS 5G SA, including UE–gNB–UPF | `docker/open5gs` | `5g-core.yaml`, `srsgnb_zmq.yaml`, `srsue_5g_zmq.yaml`, `attacker_5g.yaml` |
| E3 | Open5GS home-routed roaming | `docker/roaming_open5gs` | `core_roaming.yaml`, `srsgnb_zmq.yaml`, `srsue_5g_zmq.yaml` |
| E4 | Parallel dual-UPF, two UEs | `docker/double_upf_open5gs` | `sa-deploy.yaml`, `nr-gnb.yaml`, `nr-ue.yaml`, `nr-ue2.yaml`, `attacker.yaml` |
| E5 | free5GC with UERANSIM | `docker/my-free5gc-compose` | `docker-compose.yaml` |
| E6 | OAI-CN5G with simulated gNB/UE | `docker/my-oai` | `core.yaml`, `gnb.yaml`, `ue.yaml` |

## Open5GS E1/E2/E4 shared images

From the artifact root:

```bash
docker build -t docker_open5gs docker/open5gs/base
docker build -t docker_srslte docker/open5gs/srslte
docker build -t docker_srsran docker/open5gs/srsran
docker build -t docker_ueransim docker/open5gs/ueransim
```

Use the image aliases in the selected Compose file as the final authority.
Start the table's files in order, **from their own environment directory**, using
`docker compose -f FILE up -d` for each. Wait for the core before the gNB, then
wait for the gNB before the UE. Separate RAN files declare external networks.
After core startup, initialize subscribers using the commands above, then start
the RAN and UE. For E4, `bash scripts/seed_subscribers.sh` in its environment
directory remains an alias for the E4 initialization command. Run
`bash scripts/verify_double_upf.sh` after both UEs start.
For E1, start the EPC services with:

```bash
cd docker/open5gs
docker compose -f 4g-core.yaml up -d mongo webui hss sgwc sgwu smf upf mme pcrf metrics grafana
```

The current MME configuration also enables SGs and depends on OsmoMSC, which
starts OsmoHLR. From `docker/open5gs`, build these images with
`docker compose -f 4g-core.yaml build osmomsc osmohlr` before core startup.
E1 subscriber initialization configures
OsmoHLR as well as Open5GS. The full inherited IMS setup additionally needs
`docker_kamailio` from `docker/open5gs/ims_base`; IMS startup is outside the
paper's loop evaluation.

## E2 UE forwarding configuration

The E2 UPF self-loop uses the basic standalone deployment. The UE–gNB–UPF
instance additionally requires UE-side forwarding. After starting the E2 core,
gNB and UE, apply the following inside the `srsue_5g_zmq` container. These are the
UE initialization steps from the original experiment profile:

```bash
docker exec -it srsue_5g_zmq bash
apt install iptables -y
sysctl -w net.ipv4.conf.all.accept_local=1 net.ipv4.conf.tun_srsue.accept_local=1
iptables -t mangle -A PREROUTING -p udp --dport 2152 -j MARK --set-mark 1
ip rule add fwmark 1 table 100
ip route add default dev tun_srsue table 100
```

These settings enable the UE return path; they do not generate loop traffic.

## Open5GS E3 roaming

```bash
docker build -t docker_open5gs docker/roaming_open5gs/base
docker build -t my_srsgnb docker/roaming_open5gs/srsgnb
docker build -t my_srsue docker/roaming_open5gs/srsue
```

The `docker_open5gs` tag is shared with E1/E2/E4. Do not overwrite it while another
environment runs. Start E3's core, initialize its home subscriber using the E3
command above, then start the gNB and UE. Initialization sets LBO to false for
home-routed roaming. The srsUE patches supply the visited Serving Network Name
for RES* derivation. See the retained patch files and Dockerfile for details.

## free5GC E5

Install `gtp5g` v0.9.5 on the host first, as specified in the original deployment.
Use the core image tags in `docker-compose.yaml`. Do not assume locally rebuilt
`latest` images match the measured images. The initialization helper uses the
WebUI API and reads `config/uecfg.yaml`. Some
inherited services are unrelated to the paper (N3IWF, TNGF, N3IWUE, NEF).
They are not behind profiles in this source snapshot. For the E5 data-plane lab
use the following core service selection, then start gNB and UE in order:

```bash
cd docker/my-free5gc-compose
docker compose up -d db free5gc-upf free5gc-nrf free5gc-amf free5gc-ausf free5gc-nssf free5gc-pcf free5gc-smf free5gc-udm free5gc-udr free5gc-chf free5gc-webui in_attacker
```

Run `python3 tools/init_subscribers.py E5` from the repository root. Then, from
`docker/my-free5gc-compose`, start the gNB and wait for it to connect to the core
before starting the UE:

```bash
docker compose up -d ueransim
docker compose up -d ue
```

## OAI E6

From `docker/my-oai`, start `core.yaml`, `gnb.yaml`, then `ue.yaml` with Compose.
The gNB and UE build from `oai-uegnb-base`, pinned to OAI RAN v2.4.0. The gNB uses
host networking; the UE points to `host.docker.internal`.
MySQL imports the bundled test subscribers automatically when initializing a
new database. This import is not rerun for an existing database; changing the
UE credentials also requires updating its database record.
