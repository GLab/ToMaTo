#!/bin/bash

for distro in lucid oneiric precise quantal raring saucy squeeze wheezy; do
  case $distro in
    squeeze|wheezy)
      type=debian
      ;;
    lucid|oneiric|precise|quantal|raring|saucy)
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
