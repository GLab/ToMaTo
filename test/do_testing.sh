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

echo ""
echo ""
echo ""

for tomato_module in backend_users backend_core backend_accounting backend_debug backend_api; do
	echo ${tomato_module}
	echo "-------------"
	echo ""
	./run_tests.sh "$tomato_module"
	echo ""
done
