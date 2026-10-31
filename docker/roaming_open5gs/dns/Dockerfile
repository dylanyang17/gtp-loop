FROM debian:bookworm

# The entrypoint runs `unbound -d` without -c, so point the Debian default
# config path at the generated /opt/unbound layout the template mounts use.
RUN apt-get update && \
    apt-get install -y --no-install-recommends unbound gettext-base && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /opt/unbound/etc/unbound && \
    ln -sf /opt/unbound/etc/unbound/unbound.conf /etc/unbound/unbound.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
