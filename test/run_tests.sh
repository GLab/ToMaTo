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

# stop tomato
echo -n "stopping current ToMaTo instance... "
../docker/run/tomato-ctl.py stop > /dev/null
echo "done"

# start tomato
echo -n "starting test ToMaTo instance in $DOCKER_DIR ... "
../docker/run/tomato-ctl.py gencerts > /dev/null
../docker/run/tomato-ctl.py start > /dev/null
echo "done"

# wait for services to start
echo -n "giving services some time to start. Waiting 20 seconds... "
sleep 20
echo "done"

# todo: test which checks reachability of all tomato modules

# copy backend's key to hosts
for host in ${HOSTS}; do
	../cli/register_backend_on_host.sh http+xmlrpc://localhost:8000 $host
done

# run tests
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

# stop tomato
echo -n "stopping test ToMaTo instance... "
../docker/run/tomato-ctl.py stop > /dev/null
echo "done"

# remove files
rm -rf "$DOCKER_DIR"
