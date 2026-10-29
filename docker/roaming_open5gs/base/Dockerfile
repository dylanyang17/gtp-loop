## Stage 1: build
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Preliminary
RUN apt update && \
    apt install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    ninja-build \
    build-essential \
    flex \
    bison \
    git \
    cmake \
    libsctp-dev \
    libgnutls28-dev \
    libgcrypt-dev \
    libssl-dev \
    libmongoc-dev \
    libbson-dev \
    libyaml-dev \
    libnghttp2-dev \
    libmicrohttpd-dev \
    libcurl4-gnutls-dev \
    libnghttp2-dev \
    libtins-dev \
    libtalloc-dev \
    meson \
    libidn11-dev \
    ca-certificates \
    curl \
    gnupg

# Cloning, **patching (optional, raise the limit of buffer size)** and building Open5GS
# Version: v2.7.7
RUN git clone https://github.com/open5gs/open5gs && \
    cd open5gs && \
    git checkout 318eeb49a7dcdff733dec60e02d9c60aefca2fb9 && \
    sed -i 's/#define[[:space:]]\+OGS_MAX_PKT_LEN[[:space:]]\+2048/#define OGS_MAX_PKT_LEN                 70000/' lib/core/ogs-macros.h && \
    meson build --prefix=`pwd`/install && \
    ninja -C build install

# Installing Node.js
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=20 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt update && \
    apt install nodejs -y

# Building WebUI
RUN cd open5gs/webui && npm ci

# Stage 2: final
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Add MongoDB repository and install mongodb-org
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list && \
    apt-get update

# Preliminary
RUN apt update && \
    apt install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    ninja-build \
    build-essential \
    flex \
    bison \
    git \
    cmake \
    libsctp-dev \
    libgnutls28-dev \
    libgcrypt-dev \
    libssl-dev \
    libmongoc-dev \
    libbson-dev \
    libyaml-dev \
    libnghttp2-dev \
    libmicrohttpd-dev \
    libcurl4-gnutls-dev \
    libnghttp2-dev \
    libtins-dev \
    libtalloc-dev \
    meson \
    iptables \
    iperf \
    iperf3 \
    traceroute \
    net-tools \
    iproute2 \
    libidn11-dev \
    ca-certificates \
    curl \
    mongodb-org \
    gnupg

RUN pip3 install click

# Installing Node.js
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=20 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt update && \
    apt install nodejs -y

# Copying Open5GS
COPY --from=builder /open5gs/install /open5gs/install
COPY --from=builder /open5gs/webui /open5gs/webui
COPY --from=builder /open5gs/misc/db /open5gs/misc/db

WORKDIR /open5gs

COPY open5gs_init.sh /
CMD ["/open5gs_init.sh"]
