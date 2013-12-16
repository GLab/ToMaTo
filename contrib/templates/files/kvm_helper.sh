#!/bin/ash
#no bash in busybox

set -e

DISTRO=""
ISSUE=$(cat /target/etc/issue)
case "$ISSUE" in
  Debian*5.0*)
    DISTRO="debian_5"
    ;;
  Debian*6.0*)
    DISTRO="debian_6"
    ;;
  Debian*7*)
    DISTRO="debian_7"
    ;;
  Ubuntu*10.04*)
    DISTRO="ubuntu_1004"
    ;;
  Ubuntu*10.10*)
    DISTRO="ubuntu_1010"
    ;;
  Ubuntu*11.04*)
    DISTRO="ubuntu_1104"
    ;;
  Ubuntu*11.10*)
    DISTRO="ubuntu_1110"
    ;;
  Ubuntu*12.04*)
    DISTRO="ubuntu_1204"
    ;;
  Ubuntu*12.10*)
    DISTRO="ubuntu_1210"
    ;;
  Ubuntu*13.04*)
    DISTRO="ubuntu_1304"
    ;;
  Ubuntu*13.10*)
    DISTRO="ubuntu_1310"
    ;;
esac

cp /prepare_vm.sh /target

# Registering prepare_vm.sh for start upon next boot
case $DISTRO in
  debian_5|ubuntu*)
    cat <<EOF >/target/etc/rc2.d/S15prepare_vm
#!/bin/bash
sleep 5
/prepare_vm.sh
rm -f /prepare_vm.sh
rm -f \$0
if [ -f /etc/init.d/grub-common ]; then
  # fix for ubuntu waiting forever at boot due to fail state
  /etc/init.d/grub-common start
fi
shutdown -h now
EOF
    chmod a+x /target/etc/rc2.d/S15prepare_vm
    ;;
  debian_6|debian_7)
    cat <<EOF >/target/etc/init.d/prepare_vm
#!/bin/sh
### BEGIN INIT INFO
# Provides:          Preparing VM
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: Preparing VM
# Description:       Preparing VM
### END INIT INFO
sleep 5
/prepare_vm.sh
insserv -r /etc/init.d/prepare_vm
rm -f /prepare_vm.sh
rm -f \$0
shutdown -h now
EOF
    chmod a+x /target/etc/init.d/prepare_vm
    chroot /target insserv /etc/init.d/prepare_vm
    ;;
esac
