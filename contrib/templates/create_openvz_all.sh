#!/bin/bash

read -p "VMID: " vmid
read -p "IP: " ip

for arch in i386 amd64; do
  for dist in wheezy squeeze lucid precise raring; do
    echo -e "$dist\n\n$arch\n$vmid\n$ip\n\n\n" | ./create_openvz_template.sh
  done
done
