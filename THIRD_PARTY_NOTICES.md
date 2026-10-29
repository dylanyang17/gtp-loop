# Third-party notices

Original, independently authored contributions to gtp-loop are licensed under
[BSD-2-Clause](LICENSE), copyright (c) 2026 gtp-loop contributors. Third-party
files and modifications to them retain their applicable upstream terms. Existing
copyright and license notices are preserved.

## Included third-party material

| Material | Source and license |
|---|---|
| Open5GS deployment recipes, configurations, and helpers in `docker/open5gs`, `docker/roaming_open5gs`, and `docker/double_upf_open5gs` | Adapted from [herlesupreeth/docker_open5gs](https://github.com/herlesupreeth/docker_open5gs). Copyright (c) 2020-2025, Supreeth Herle. [BSD-2-Clause](docker/open5gs/LICENSE), except for separately licensed upstream material identified below or in file headers. |
| free5GC deployment files in `docker/my-free5gc-compose` | Adapted from [free5gc/free5gc-compose](https://github.com/free5gc/free5gc-compose/tree/v4.2.1). [Apache-2.0](docker/my-free5gc-compose/LICENSE.txt). Modified copies carry change notices. |
| `docker/open5gs/srsran/srsran_performance` and `docker/roaming_open5gs/srsgnb/srsran_performance` | From [srsRAN Project](https://github.com/srsran/srsRAN_Project). Copyright 2021-2025 Software Radio Systems Limited. [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt). |
| `docker/my-oai/conf/config.yaml` | OpenAirInterface Software Alliance. [OAI Public License 1.1](LICENSES/OAI-Public-License-1.1.txt). The upstream [NOTICE](LICENSES/OAI-NOTICE.md) is included. |
| Kamailio and SEMS configuration examples in `docker/open5gs/icscf`, `docker/open5gs/scscf`, `docker/open5gs/pcscf`, and `docker/open5gs/smsc` | Retained through docker_open5gs from [Kamailio](https://github.com/kamailio/kamailio) and [SEMS](https://github.com/sems-server/sems). Their upstream terms and retained notices apply; see [Kamailio COPYING](LICENSES/Kamailio-COPYING.txt) and the [SEMS COPYING](LICENSES/SEMS-COPYING.txt). |
| PyHSS templates and configuration in `docker/open5gs/pyhss` | Retained through docker_open5gs from [PyHSS](https://github.com/nickvsnetworking/pyhss), under its [AGPL-3.0 license](https://github.com/nickvsnetworking/pyhss/blob/master/LICENSE). The BSD notices on deployment helpers do not replace the PyHSS license. |

Other configuration examples retain the licenses and notices of their respective
upstream projects. The repository's BSD license does not replace these terms.

The public test certificates and keys in `docker/my-free5gc-compose/cert` are
copied verbatim from [free5gc-compose v4.2.1](https://github.com/free5gc/free5gc-compose/tree/v4.2.1/cert)
and retain its Apache-2.0 license.

## Authored srsRAN patches

The following patches modify srsRAN 4G at revision
`ec29b0c1ff79cebcbe66caa6d6b90778261c42b8` to support a configurable visited
Serving Network Name for roaming authentication:

- `docker/roaming_open5gs/srsue/lib.patch`
- `docker/roaming_open5gs/srsue/srsue.patch`

Both patches are licensed under [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt),
matching the affected upstream files. Upstream code is copyright 2013-2023
Software Radio Systems Limited. Modifications are copyright (c) 2026 gtp-loop
contributors. The patch headers identify the modification date and base revision.

The Open5GS packet-buffer adjustment is applied by the base Dockerfiles when
building Open5GS. The resulting Open5GS source remains subject to its upstream
[AGPL-3.0 license](https://github.com/open5gs/open5gs/blob/v2.7.7/LICENSE).

## Software downloaded or built by the recipes

Dockerfiles download upstream software, and Compose files reference upstream
container images. Those projects and images retain their own licenses; the
repository's BSD license does not license their contents. The Dockerfiles and Compose files identify the source revisions and image tags
used by each recipe.
