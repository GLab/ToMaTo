#!/bin/bash

for distro in lucid oneiric precise squeeze; do
  case $distro in
    squeeze)
      type=debian
      ;;
    lucid|oneiric|precise)
      type=ubuntu
      ;;
  esac
  for arch in i386 amd64; do
    mkdir -p $distro/$arch
    for file in linux initrd.gz; do
      wget -c ftp://ftp.uni-kl.de/pub/linux/$type/dists/$distro/main/installer-$arch/current/images/netboot/$type-installer/$arch/$file -O $distro/$arch/$file
    done
  done
done