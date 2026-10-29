#!/bin/bash
set -e

if [ -f .env ]; then
	set -a          # 自动 export
	source .env
	set +a
fi

OUT=./tls/
mkdir -p $OUT

echo "==> Generating CA"
openssl genrsa -out $OUT/ca.key 4096
openssl req -x509 -new -nodes -key $OUT/ca.key -sha256 -days 36500 \
	-subj "/C=KR/ST=Seoul/O=Open5GS/CN=Open5GS-CA" \
	-out $OUT/ca.crt

echo "==> Generating HSEPP private key"
openssl genrsa -out $OUT/hsepp.key 2048

echo "==> Generating HSEPP CSR"
openssl req -new -key $OUT/hsepp.key \
	-subj "/C=KR/ST=Seoul/O=Open5GS/CN=sepp.5gc.mnc${HMNC}.mcc${HMCC}.3gppnetwork.org" \
	-out $OUT/hsepp.csr

echo "==> Signing HSEPP certificate"
openssl x509 -req -in $OUT/hsepp.csr -CA $OUT/ca.crt -CAkey $OUT/ca.key \
	-CAcreateserial -out $OUT/hsepp.crt -days 36500 -sha256

echo "==> Generating VSEPP private key"
openssl genrsa -out $OUT/vsepp.key 2048

echo "==> Generating VSEPP CSR"
openssl req -new -key $OUT/vsepp.key \
	-subj "/C=KR/ST=Seoul/O=Open5GS/CN=sepp.5gc.mnc${VMNC}.mcc${VMCC}.3gppnetwork.org" \
	-out $OUT/vsepp.csr

echo "==> Signing HSEPP certificate"
openssl x509 -req -in $OUT/vsepp.csr -CA $OUT/ca.crt -CAkey $OUT/ca.key \
	-CAcreateserial -out $OUT/vsepp.crt -days 36500 -sha256

echo "Done!"
echo "Generated files:"
ls -l $OUT

