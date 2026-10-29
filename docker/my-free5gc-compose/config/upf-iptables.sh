#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Modified for gtp-loop on 2026-10-28: deployment and public test configuration.
#
# Configure iptables in UPF
#
iptables -t nat -A POSTROUTING -o eth0  -j MASQUERADE
iptables -I FORWARD 1 -j ACCEPT

