#!/bin/bash
if [ "$1" == "" ]; then
  echo "Usage $0 ARCHIVE"
  exit 1
fi
echo "Building $1:"
../../cli/getpackages.py -h master.tomato-lab.org --ssl -t $1.tar.gz --packetconfig configs/$1.json
