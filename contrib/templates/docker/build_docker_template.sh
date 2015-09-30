#!/bin/bash

set -e

NAME=$1
OUTPUT=${NAME}_x86_64.tar.gz

if [ "$NAME" == "" ]; then
  echo "Usage: $0 NAME"
  exit 1
fi

if ! [ -d $NAME ]; then
  echo "Build directory for $NAME does not exist"
  exit 1
fi

make -C .. prepare_vm.sh
cp -a ../prepare_vm.sh $NAME/prepare_vm.sh
docker build --rm -t $NAME $NAME
docker run -d --name $NAME $NAME bash -c 'while true; do sleep 1; done'
ID=$(docker inspect --format='{{.Id}}' $NAME)
MOUNTDIR=/var/lib/docker/aufs/mnt/$ID
sudo tar -czf `pwd`/$OUTPUT --numeric-owner -C $MOUNTDIR .
docker stop $NAME
docker rm $NAME
