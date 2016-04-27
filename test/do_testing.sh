#!/bin/bash
cd "$(dirname "$0")"

# read the docker dir from local tomato-ctl.conf
DOCKER_DIR=$(echo '
import json
with open("tomato-ctl.conf") as f:
 config = json.load(f)
print config["docker_dir"]' | python -)

# read host list
HOSTS=$(echo '
import json
with open("testhosts.json") as f:
 hosts = json.load(f)
print " ".join(hosts)' | python -)

if [ -e "$DOCKER_DIR" ]; then
	echo "ERROR: Please remove $DOCKER_DIR before starting."
	exit 1
fi

echo ""
echo ""
echo ""
echo "backend_users"
echo "-------------"
echo ""
python -m unittest -v backend_users
echo ""
echo ""
echo ""
echo ""
echo "backend_core"
echo "-------------"
echo ""
python -m unittest -v backend_core
echo ""
echo ""
echo ""
echo ""
echo "backend_accounting"
echo "-------------"
echo ""
python -m unittest -v backend_accounting
echo ""
echo ""
echo ""
echo ""
echo "backend_debug"
echo "-------------"
echo ""
python -m unittest -v backend_debug
echo ""
echo ""
echo ""
echo ""
echo "backend_api"
echo "-------------"
echo ""
python -m unittest -v backend_api
echo ""
echo ""
echo ""
