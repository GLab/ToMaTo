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
echo -n "stopping test ToMaTo instance... "
../docker/run/tomato-ctl.py stop > /dev/null
echo "done"

# remove files
rm -rf "$DOCKER_DIR"
if [ -e "$DOCKER_DIR" ]; then
	echo "failed removing $DOCKER_DIR"
	echo "Please remove it before running the next test."
fi
