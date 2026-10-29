#!/bin/bash
set -euo pipefail

RFSIM_SERVER_ADDR="${RFSIM_SERVER_ADDR:-host.docker.internal}"

cd ~/openairinterface5g/cmake_targets/ran_build/build
./nr-uesoftmodem --rfsim --rfsimulator.serveraddr "$RFSIM_SERVER_ADDR" -r 106 --numerology 1 --band 78 -C 3619200000 -O /nrue.uicc.conf
