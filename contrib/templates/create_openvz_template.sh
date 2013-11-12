#!/bin/bash

# can be automated via:
# echo -e "precise\n\n\n333\n131.246.112.93\n\n\n" | ./create_debian_openvz_template.sh

set -e

if [ $EUID -gt 0 ]; then
  echo "Must be run as root, trying sudo..."
  exec sudo "$0" "$@"
fi

for dep in debootstrap vzctl; do
  if ! (dpkg-query -s $dep | fgrep -q installed); then
    fail "Dependency missing: $dep"
  fi
done

function get() {
  varname="$1"
  msg="$2"
  default="$3"
  if [ -z "$default" ]; then
    msg="$msg: "
  else
    msg="$msg [$default]: "
  fi
  read -e -p "$msg" value
  [ -z "$value" ] && value="$default"
  export $varname=$value
}

function fail() {
  msg="$1"
  code=$2
  if [ -z "$code" ]; then
    code=255
  fi
  echo "$msg" >&2
  exit $code
}

get DISTRO "Distribution (codename)"
case "$DISTRO" in
  squeeze|wheezy)
    TYPE="debootstrap"
    MIRROR="ftp://ftp.debian.org/debian"
    COMPONENTS="main"
    ;;
  lucid|natty|oneiric|precise|quantal|raring|saucy)
    TYPE="debootstrap"
    MIRROR="http://archive.ubuntu.com/ubuntu"
    COMPONENTS="main,universe"
    #workaround for older systems that dont know about newer ubuntu versions
    if ! [ -f /usr/share/debootstrap/scripts/$DISTRO ]; then
      for dist in lucid natty oneiric precise quantal raring saucy; do
        cp /usr/share/debootstrap/scripts/$dist /usr/share/debootstrap/scripts/$DISTRO
      done
    fi
    ;;
  fedora-17)
    TYPE="febootstrap"
    MIRROR="" #too complicate to determine
    ;;
  *) fail "Unknown distribution: $DISTRO"
esac

get MIRROR "Mirror" "$MIRROR"

get ARCH "Architecture (amd64,i386)" amd64
case "$ARCH" in
  amd64|i386)
    ;;
  *) fail "Unknown architecture: $ARCH"
esac

get VMID "VM ID"
TARGET=/var/lib/vz/private/$VMID
MOUNT=/var/lib/vz/root/$VMID
[ -d "$TARGET" ] && fail "VM $VMID already exists"

get IP4ADDRESS "IP Address"
ping "$IP4ADDRESS" -q -c 1 -W 1 >/dev/null && fail "IP address is already used: $IP4ADDRESS"

DEST="$DISTRO-$ARCH.tar.gz"
get DEST "Destination" "$DEST"
[ -f "$DEST" ] && fail "Destination file already exists: $DEST"


echo
get DUMMY "Press ENTER to start"

set -e

mkdir -p "$TARGET"

echo
echo "Fetching and installing packages..."
case $TYPE in
  debootstrap)
    debootstrap --arch $ARCH --components "$COMPONENTS" $DISTRO "$TARGET" "$MIRROR" 2>&1
    ;;
  febootstrap)
    febootstrap $DISTRO "$TARGET" "$MIRROR" 2>&1
    ;;
esac

echo
echo "Configuring VM container..."
vzctl set $VMID --applyconfig basic --save || vzctl set $VMID --applyconfig default --save
echo 'OSTEMPLATE=\"debian-5.0\"' >> /etc/vz/conf/$VMID.conf
vzctl set $VMID --ipadd $IP4ADDRESS --save
[ -e $TARGET/dev/ptmx ] || mknod --mode 666 $TARGET/dev/ptmx c 5 2
vzctl set $VMID --nameserver 8.8.8.8 --save

echo
echo "Starting VM container..."
# Kill all processes that might be left-over from the bootstrap process
mkdir -p "$MOUNT"
lsof | fgrep "$TARGET" | cut -b12-20 | uniq | xargs -r kill
vzctl start $VMID
for i in seq 1 10; do
  # Wait for network connectivity (fix for --wait bug in openvz)
  if vzctl exec2 $VMID ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    break
  fi
  # Add ip address again if it is not there (fix for ubuntu problem)
  if ! vzctl exec $VMID ifconfig | fgrep -q $IP4ADDRESS; then
    vzctl set $VMID --ipadd $IP4ADDRESS
  fi
done
vzctl exec2 $VMID ping -c 1 -W 10 8.8.8.8 >/dev/null 2>&1

echo
echo "Preparing VM contents..."
cp files/prepare_vm.sh "$TARGET/run.sh"
vzctl exec2 $VMID /run.sh 2>&1; R=$?
[ $R -eq 0 ] #check return code (set -e will exit here)
rm "$TARGET/run.sh"

echo
echo "Creating template tarball..."
tar --numeric-owner -czf "$DEST" -C "$TARGET" .

if ! [ "$1" == "--nodelete" ]; then
  echo
  echo "Destroying VM container..."
  vzctl stop $VMID
  vzctl destroy $VMID
fi

echo
echo "Size of archive: $(ls -lh $DEST | awk {'print $5'})"
echo
echo "Finished."
