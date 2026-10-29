FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        tcpdump \
        iproute2 \
        iputils-ping \
        libpcap-dev \
        vim \
        tmux \
    && rm -rf /var/lib/apt/lists/*


CMD ["sleep", "infinity"]
