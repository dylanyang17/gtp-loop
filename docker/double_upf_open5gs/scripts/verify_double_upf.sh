#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[compose] validating YAML"
docker compose -f sa-deploy.yaml config >/dev/null
docker compose -f nr-gnb.yaml config >/dev/null
docker compose -f nr-ue.yaml config >/dev/null
docker compose -f nr-ue2.yaml config >/dev/null

echo "[config] checking single SMF with two UPF PFCP clients"
grep -q "address: UPF_IP" smf/smf.yaml
grep -q "address: UPF2_IP" smf/smf.yaml
grep -q "dnn: internet" smf/smf.yaml
grep -q "dnn: private" smf/smf.yaml

echo "[config] checking UE-to-slice/DNN intent"
grep -q "apn: 'internet'" ueransim/ueransim-ue.yaml
grep -q "sd: 0x000001" ueransim/ueransim-ue.yaml
grep -q "apn: 'private'" ueransim/ueransim-ue2.yaml
grep -q "sd: 0x000002" ueransim/ueransim-ue2.yaml

if docker inspect double_upf_smf >/dev/null 2>&1; then
  echo "[runtime] checking SMF/UPF containers"
  docker ps --format '{{.Names}}' | grep -Eq '^double_upf_smf$'
  docker ps --format '{{.Names}}' | grep -Eq '^double_upf_upf1$'
  docker ps --format '{{.Names}}' | grep -Eq '^double_upf_upf2$'

  smf_logs="$(docker logs --tail 400 double_upf_smf 2>&1)"
  upf1_logs="$(docker logs --tail 200 double_upf_upf1 2>&1)"
  upf2_logs="$(docker logs --tail 200 double_upf_upf2 2>&1)"

  echo "[runtime] checking PFCP associations"
  grep -q "PFCP associated \\[172.24.0.8\\]:8805" <<<"$smf_logs"
  grep -q "PFCP associated \\[172.24.0.90\\]:8805" <<<"$smf_logs"

  if docker inspect double_upf_nr_ue1 >/dev/null 2>&1 && docker inspect double_upf_nr_ue2 >/dev/null 2>&1; then
    echo "[runtime] checking UE session to UPF mapping"
    grep -q "UE SUPI\\[imsi-001011224567895\\] DNN\\[internet\\] IPv4\\[192.168.100.2\\]" <<<"$smf_logs"
    grep -q "gtp_connect() \\[172.24.0.8\\]:2152" <<<"$smf_logs"
    grep -q "UE SUPI\\[imsi-001011224567896\\] DNN\\[private\\] IPv4\\[192.168.102.2\\]" <<<"$smf_logs"
    grep -q "gtp_connect() \\[172.24.0.90\\]:2152" <<<"$smf_logs"
    grep -q "APN\\[internet\\].*IPv4\\[192.168.100.2\\]" <<<"$upf1_logs"
    grep -q "APN\\[private\\].*IPv4\\[192.168.102.2\\]" <<<"$upf2_logs"
    docker exec double_upf_nr_ue1 ip -4 addr show uesimtun0 | grep -q "192.168.100.2"
    docker exec double_upf_nr_ue2 ip -4 addr show uesimtun0 | grep -q "192.168.102.2"
  else
    echo "[runtime] UE containers are not running; PFCP association verified only"
  fi
else
  echo "[runtime] core is not running; static validation only"
fi
