#!/bin/bash

for arch in amd64; do
  while read dist; do
    echo -e "$arch\n$dist\n\n\n" | ./create_kvm_template.sh "$@"
  done < distros.build.txt
done
