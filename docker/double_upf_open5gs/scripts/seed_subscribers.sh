#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 gtp-loop contributors.
set -euo pipefail
cd "$(dirname "$0")/../../.."
exec python3 tools/init_subscribers.py E4 "$@"
