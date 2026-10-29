#!/bin/sh
set -e

envsubst < /opt/unbound/etc/unbound/unbound.conf.template > /opt/unbound/etc/unbound/unbound.conf

exec unbound -d
