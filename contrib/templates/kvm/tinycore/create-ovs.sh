#!/bin/sh

OVS_COMMIT=v2.5.0
TUNCTL_VERSION=1.5
BRIDGE_UTILS_VERSION=1.5

set -e

silent() {
  OUT=/tmp/out
  set +e
  "$@" >$OUT 2>&1
  RES=$?
  set -e
  if [ $RES != 0 ]; then
    echo "Command $@ failed with error $RES. Output is recorded in $OUT. Last lines were:"
    tail $OUT
  fi
  return $RES
}

download() {
  FILE="$1"
  URL="$2"
  [ -f $FILE ] || silent wget "$URL" -O "$FILE"
}

expect_ret() {
  EXPECTED=$1
  shift
  "$@"
  RES=$?
  if [ $RES == $EXPECTED ]; then
    return 0
  else
    echo "Command $@ returned error code $RES instead of $EXPECTED"
    return 1
  fi
}

install() {
  silent tce-load -wi "$@"
}

echo "Installing build env into ram..."
cd /root
rm /etc/sysconfig/tcedir; ln -s /tmp /etc/sysconfig/tcedir
install compiletc perl5 autoconf automake openssl-dev linux-kernel-sources-env libtool libtool-dev python squashfs-tools
silent linux-kernel-sources-env.sh
export CFLAGS="-march=i486 -mtune=i686 -Os -pipe"
export CXXFLAGS="-march=i486 -mtune=i686 -Os -pipe"
export CPPFLAGS="-march=i486 -mtune=i686 -Os -pipe"
export LDFLAGS="-Wl,-O1"

echo "Building openvswitch..."
cd /root
download ovs.tar.gz https://github.com/openvswitch/ovs/archive/$OVS_COMMIT.tar.gz
tar -xzf ovs.tar.gz
cd ovs-*
silent ./boot.sh
silent ./configure --with-linux=/lib/modules/`uname -r`/build
silent make
mkdir -p /root/openvswitch
silent make DESTDIR=/root/openvswitch PREFIX=/ install
silent sudo make modules_install
cd /root/openvswitch
mkdir -p lib/modules/`uname -r`/extra/
sudo cp -a /lib/modules/`uname -r`/extra/*.ko lib/modules/`uname -r`/extra/

echo "Building tunctl..."
cd /root
download tunctl.tar.gz http://downloads.sourceforge.net/project/tunctl/tunctl/$TUNCTL_VERSION/tunctl-$TUNCTL_VERSION.tar.gz
tar -xzf tunctl.tar.gz
cd tunctl-*
touch tunctl.8
silent make
mkdir -p /root/tunctl
silent make DESTDIR=/root/tunctl PREFIX=/ install

echo "Building bridge-utils..."
cd /root
download bridge-utils.tar.gz http://downloads.sourceforge.net/project/bridge/bridge/bridge-utils-$BRIDGE_UTILS_VERSION.tar.gz
download bridge-utils-1.5-linux_3.8_fix-1.patch http://www.linuxfromscratch.org/patches/blfs/svn/bridge-utils-1.5-linux_3.8_fix-1.patch
tar -xzf bridge-utils.tar.gz
cd bridge-utils-*
silent patch -Np1 -i ../bridge-utils-1.5-linux_3.8_fix-1.patch
silent autoconf -o configure configure.in
silent ./configure --with-linux-headers=/usr/src/linux-`uname -r`/arch/x86
silent make
mkdir -p /root/bridge-utils
silent make DESTDIR=/root/bridge-utils PREFIX=/ install

echo "Creating packages..."
cd /root
silent mksquashfs openvswitch /mnt/sda1/tce/optional/openvswitch.tcz
cat > /mnt/sda1/tce/optional/openvswitch.tcz.dep <<END
gcc_libs.tcz
openssl.tcz
tunctl.tcz
bridge-utils.tcz
END
silent mksquashfs tunctl /mnt/sda1/tce/optional/tunctl.tcz
silent mksquashfs bridge-utils /mnt/sda1/tce/optional/bridge-utils.tcz

echo "Configuring system..."
cat >/opt/bootsync.sh <<END
#!/bin/sh
# put other system startup commands here

/usr/bin/sethostname ofswitch

export PATH="\$PATH:/usr/local/sbin:/usr/local/bin"

modprobe openvswitch
modprobe 8021q
modprobe ipv6
DATABASE=/opt/ovs.db
if ! [ -f \$DATABASE ]; then
  ovsdb-tool create \$DATABASE
fi
ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock --pidfile --detach \$DATABASE
ovs-vsctl --no-wait init
ovs-vswitchd --pidfile --detach
if ! \$(ovs-vsctl list-br | fgrep br0 >/dev/null); then
  ovs-vsctl add-br br0
  ovs-vsctl set-controller br0 ptcp:6633
  ovs-vsctl set bridge br0 protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13,OpenFlow14,OpenFlow15
fi
for path in /proc/sys/net/ipv4/conf/eth*; do
  iface=\$(basename \$path)
  ifconfig \$iface up
  if ! \$(ovs-vsctl list-ports br0 | fgrep \$iface >/dev/null); then
    ovs-vsctl add-port br0 \$iface
  fi
done
if [ -f "/opt/address" ]; then
 ifconfig br0 \$(cat /opt/address) up
fi
if [ -f "/opt/kmap" ]; then
 loadkmap < /usr/share/kmap/\$(cat /opt/kmap).kmap
fi

/opt/bootlocal.sh &
END
cat >/opt/bootlocal.sh <<END
#!/bin/sh
# put other system startup commands here
while true; do
  filetool.sh -bs >/dev/null
  sleep 10
done
END
cat >>/root/.profile <<END
alias save="filetool.sh -bs >/dev/null"
address() {
  ifconfig br0 "\$1" up
  echo "\$1" >/opt/address
  save
}
kmap() {
  LANG="\$1"
  FILE="/usr/share/kmap/\$1.kmap"
  if [ -f "\$FILE" ]; then
    loadkmap < "\$FILE"
    echo "\$LANG" >/opt/kmap
    save
  else
    echo "Kmap not found"
  fi
}
alias controller="ovs-vsctl set-controller br0"
ovs() {
  CMD="\$1"
  shift
  ovs-vsctl "\$CMD" br0 "\$@"
}
of() {
  CMD="\$1"
  shift
  ovs-ofctl "\$CMD" br0 "\$@"
}
END
sed -e 's/kmap=qwertz\/de-latin1-nodeadkeys/kmap=qwerty\/us/' -i /mnt/sda1/tce/boot/extlinux/extlinux.conf
echo "/root/.profile" >> /opt/.filetool.lst
silent expect_ret 1 filetool.sh -b
rm /etc/sysconfig/tcedir; ln -s /mnt/sda1/tce /etc/sysconfig/tcedir
install ipv6-$(uname -r)
cp /tmp/optional/gcc_libs.tcz* /tmp/optional/openssl.tcz* /mnt/sda1/tce/optional

echo openvswitch >> /mnt/sda1/tce/onboot.lst

echo "done."
#sudo poweroff
