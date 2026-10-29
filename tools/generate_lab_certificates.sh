#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 gtp-loop contributors.
set -euo pipefail
cd "$(dirname "$0")/.."
(
 cd docker/roaming_open5gs
 if [ ! -f tls/ca.key ]; then bash generate_sepp_keys.sh; bash move_sepp_keys.sh; fi
)
echo 'Local SEPP certificates generated.'
