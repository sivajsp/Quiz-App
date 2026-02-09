#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

node_count=$1

if ! [ "$node_count" -eq "$node_count" ] 2> /dev/null; then
  # default to 3 nodes
  node_count=3
fi

required_certs=(
  "admin"
  "isg-service"
  "dashboard-client"
  "dashboard-server"
  "ingest-server"
)


function generate_certificate() {
  openssl genrsa -out $1-key-temp.pem 2048
  openssl pkcs8 -inform PEM -outform PEM -in $1-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out $1-key.pem
  openssl req -new -key $1-key.pem -subj "/C=CA/ST=ONTARIO/L=TORONTO/O=ISG/OU=ISG/CN=$1.infosecglobal.com" -out $1.csr
  echo "subjectAltName=DNS:$1.infosecglobal.com" > $1.ext
  openssl x509 -req -in $1.csr -CA rootca.pem -CAkey rootca-key.pem -CAcreateserial -sha256 -out $1.pem -days 730 -extfile $1.ext
  rm $1-key-temp.pem
  rm $1.csr
  rm $1.ext
}

# Root CA
openssl genrsa -out rootca-key.pem 2048
openssl req -new -x509 -sha256 -key rootca-key.pem -subj "/C=CA/ST=ONTARIO/L=TORONTO/O=ISG/OU=ISG/CN=root.infosecglobal.com" -out rootca.pem -days 730

for cert in "${required_certs[@]}"
do
  generate_certificate $cert
done

for ((i=1; i<=node_count; i++))
do
  generate_certificate "node$i"
done