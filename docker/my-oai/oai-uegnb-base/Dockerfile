FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Preliminary
RUN apt update && \
    apt install -y autoconf automake build-essential ccache cmake cpufrequtils doxygen ethtool g++ git inetutils-tools libboost-all-dev libncurses-dev libusb-1.0-0 libusb-1.0-0-dev libusb-dev python3-dev python3-mako python3-numpy python3-requests python3-scipy python3-setuptools python3-ruamel.yaml libforms-dev libforms-bin

# Cloning and Build
# Version: v2.4.0
RUN git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git ~/openairinterface5g && \
    cd ~/openairinterface5g && \
    git checkout v2.4.0 && \
    cd cmake_targets && \
    ./build_oai -I && \
    ./build_oai -w SIMU --ninja --nrUE --gNB --build-lib "nrscope" -C

RUN apt install -y python3 vim tmux iputils-ping iproute2 python3-pip

CMD ["/init.sh"]
