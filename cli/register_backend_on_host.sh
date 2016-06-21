#!/bin/bash
cd "$(dirname "$0")"

if [ "$#" -ne 3 ]; then
    echo "usage: $0 BACKEND_URL HOST_ADDRESS CERT_IDENTIFIER"
    exit 1
fi

echo '
print server_info()["public_key"]
' > /tmp/register_backend_on_host__extract_key.py

./tomato.py --url $1 -f /tmp/register_backend_on_host__extract_key.py > /tmp/register_backend_on_host__key.pem
scp /tmp/register_backend_on_host__key.pem root@$2:/etc/tomato/client_certs/$(hostname)_$3.pem
ssh root@$2 update-tomato-client-certs
