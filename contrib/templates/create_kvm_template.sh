#!/bin/bash

# can be automated via:
# echo -e "precise\n\n\n333\n131.246.112.93\n\n\n" | ./create_kvm_template.sh

if [ $EUID -gt 0 ]; then
  echo "Must be run as root, trying sudo..."
  exec sudo "$0" "$@"
fi

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

get ARCH "Architecture (amd64,i386)" amd64
case "$ARCH" in
  amd64)
    CPU=kvm64
    ;;
  i386)
    CPU=kvm32
    ;;
  *) fail "Unknown architecture: $ARCH"
esac

get DISTRO "Distribution (nickname)" precise
case "$DISTRO" in
  squeeze|wheezy|lucid|natty|oneiric|precise|quantal|raring|saucy)
    PRESEED="/$DISTRO.preseed.txt"
    KERNEL="boot/$DISTRO/$ARCH/linux"
    INITRD="boot/$DISTRO/$ARCH/initrd.gz"
    ;;
  *) fail "Unknown distribution: $DISTRO"
esac

get SIZE "Disk size" 10G

DEST="$DISTRO-$ARCH.qcow2"
get DEST "Destination" "$DEST"
[ -f "$DEST" ] && fail "Destination file already exists: $DEST"

KVM="kvm -usbdevice tablet -m 512 -smp sockets=1,cores=1 -nodefaults -vga cirrus -tdf -k de -enable-kvm -net nic,model=e1000 -net user"
if ! [ "$1" == "--observe" ]; then
  KVM="$KVM -display none"
fi
APPEND="auto locale=en_US.UTF-8 console-keymaps-at/keymap=de keymap=de priority=critical vga=788"

echo
get DUMMY "Press ENTER to start"

set -e

echo
echo "Creating VM disk..."
qemu-img create -f qcow2 $DEST $SIZE

echo
echo "Creating ramdisk..."
mkdir ramdisk
gunzip < $INITRD | (cd ramdisk; cpio --extract)
cp -a files/* ramdisk
(cd ramdisk; find . | cpio --create --'format=newc' ) | gzip > ramdisk.gz
rm -rf ramdisk

echo
echo "Starting VM autoinstall..."
$KVM -cpu $CPU -hda $DEST -kernel $KERNEL -initrd ramdisk.gz -append "$APPEND preseed/url=file://$PRESEED"

echo
echo "Removing ramdisk..."
rm ramdisk.gz

echo
echo "Preparing VM contents..."
$KVM -cpu $CPU -hda $DEST

echo
echo "Compressing disk image..."
echo "  - Raw size of disk image: $(ls -lh $DEST | awk {'print $5'})"
mv $DEST $DEST.raw
qemu-img convert -c -O qcow2 $DEST.raw $DEST
rm $DEST.raw
echo "  - Size of disk image: $(ls -lh $DEST | awk {'print $5'})"

echo
echo "Finished."
