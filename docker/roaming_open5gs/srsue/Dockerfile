# BSD 2-Clause License

# Copyright (c) 2020-2025, Supreeth Herle
# All rights reserved.

# Redistribution and use in binary form, with or without
# modification, is permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# ZMQ radio dependencies only (no SDR hardware drivers)
RUN apt-get update && \
    apt-get -y install cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev git \
    libzmq3-dev libboost-system-dev libboost-test-dev libboost-thread-dev \
    g++ make pkg-config net-tools iputils-ping iproute2

# Get srsLTE
RUN git clone https://github.com/srsran/srsRAN_4G.git

# srsLTE: **patch (to solve Serving Network Name issue)**, compile and install
COPY srsue.patch /srsue.patch
COPY lib.patch /lib.patch
RUN cd srsRAN_4G && \
    git checkout ec29b0c1ff79cebcbe66caa6d6b90778261c42b8 && \
    cd srsue && patch -p1 < /srsue.patch && cd .. && \
    cd lib && patch -p1 < /lib.patch && cd .. && \
    mkdir build && cd build && \
    cmake ../ && make -j`nproc` && make install && \
    ldconfig

RUN cd srsRAN_4G/build && srsran_install_configs.sh service

# install python for running custom scripts
RUN apt install -y python3 python3-pip vim tmux

# solve Chinese display issue
ENV LANG=C.UTF-8

CMD ["/mnt/srslte/srslte_init.sh"]
