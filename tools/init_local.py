# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 gtp-loop contributors.
"""Create ignored local configs; never replace an existing file."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for src in root.rglob('*.env.example'):
    dst = src.with_suffix('')
    if not dst.exists():
        dst.write_bytes(src.read_bytes())
        print('Created', dst.relative_to(root))
