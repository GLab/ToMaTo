#!/bin/bash

for name in `ls .`; do
  if [ -d "$name" ]; then
    ./create_docker_template.sh "$@"
  fi
done
