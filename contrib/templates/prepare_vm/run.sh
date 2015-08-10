#!/bin/bash

function fail() {
  msg="$1"
  code=$2
  if [ -z "$code" ]; then
    code=255
  fi
  echo "$msg" >&2
  exit $code
}

set -e

VMTYPE=""
if [ -d /proc/vz ]; then
  VMTYPE="openvz"
fi
if fgrep -q docker /proc/1/cgroup; then
  VMTYPE="openvz"
fi
if dmesg | fgrep -q QEMU; then
  VMTYPE="kvm"
fi
if [ -z "$VMTYPE" ]; then
  fail "Unknown VM type"
fi
echo "VM type: $VMTYPE"

DISTRO=""
ISSUE=$(cat /etc/issue)
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
  Debian*8*)
    DISTRO="debian_8"
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
  Ubuntu*14.04*)
    DISTRO="ubuntu_1404"
    ;;
  Ubuntu*14.10*)
    DISTRO="ubuntu_1410"
    ;;
  Ubuntu*15.04*)
    DISTRO="ubuntu_1504"
    ;;
  Ubuntu*15.10*)
    DISTRO="ubuntu_1510"
    ;;
  *)
    fail "Unknown distribution: $ISSUE"
esac
echo "Distribution: $DISTRO"

echo

echo "Updating system..."
case $DISTRO in
  debian*|ubuntu*)
    apt-get update
    apt-get upgrade -y
    ;;
  *)
    fail "$DISTRO unsupported"
esac


# Packages: ssh nano iperf tcpdump screen vim-tiny locales manpages man-db less
echo "Installing packages..."
case $DISTRO in
  debian*|ubuntu*)
    apt-get install --no-install-recommends -y ssh nano iperf tcpdump screen vim-tiny locales manpages man-db less
    ;;
  *)
    fail "$DISTRO unsupported"
esac


echo "Disabling services..."
case $DISTRO in
  ubuntu*)
    service rsyslog stop || true
    update-rc.d -f rsyslog remove
    service ssh stop || true
    update-rc.d -f ssh remove
    echo "manual" > /etc/init/ssh.override
    cat <<EOF >/usr/local/bin/ssh-enable
#!/bin/bash
set -e
echo "Please select a secure root password"
passwd root
rm /etc/init/ssh.override
service ssh start
EOF
    chmod +x /usr/local/bin/ssh-enable
    ;;
  debian*)
    /etc/init.d/rsyslog stop || true
    update-rc.d -f rsyslog remove
    /etc/init.d/ssh stop || true
    update-rc.d -f ssh remove
    cat <<EOF >/usr/local/bin/ssh-enable
#!/bin/bash
set -e
echo "Please select a secure root password"
passwd root
update-rc.d ssh defaults
/etc/init.d/ssh start
EOF
    chmod +x /usr/local/bin/ssh-enable
    update-rc.d -f inetd remove
    ;;
  *)
    fail "$DISTRO unsupported"
esac
# check that only allowed services are running
if netstat -tulpen | grep -e '\(::\)\|\(0\.0\.0\.0\)' | fgrep -v ntpdate | fgrep -v dhclient; then
  fail "The following services are still running: $(netstat -tulpen | grep -e '\(::\)\|\(0\.0\.0\.0\)')"
fi


echo "Applying some configuration changes..."
# Disable sync() for syslog -> performance
sed -i -e 's@\([[:space:]]\)\(/var/log/\)@\1-\2@' /etc/*syslog.conf
# Timezone = Europe/Berlin
ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime


echo "Auto-login on consoles..."
case $DISTRO in
  ubuntu*|debian*)
    apt-get install --no-install-recommends -y mingetty
    for file in /etc/inittab /etc/init/tty1.conf "/etc/systemd/system/getty.target.wants/getty@tty1.service"; do
      if [ -f "$file" ]; then
        sed -i -e 's/\/sbin\/getty\( -8\)\? 38400/\/sbin\/mingetty --autologin root --noclear/g' "$file"
        sed -i -e 's/ExecStart=-\/sbin\/agetty/ExecStart=-\/sbin\/mingetty --autologin root/g' "$file"
      fi
    done
    ;;
esac


# locale: en_US.UTF-8
echo "Setting locale..."
case $DISTRO in
  ubuntu*|debian*)
    cat <<EOF > /etc/default/locale
LANG=en_US.UTF-8
LANGUAGE=en_US.UTF-8
EOF
    case $DISTRO in
      ubuntu*)
        locale-gen en_US.UTF-8
        ;;
      debian*)
        rm -f /etc/locale.gen #debian needs this
        ;;
    esac
    debconf-set-selections <<EOF
debconf locales/default_environment_locale select en_US.UTF-8
debconf locales/locales_to_be_generated multiselect en_US.UTF-8 UTF-8
EOF
    dpkg-reconfigure -f noninteractive locales
    cat <<EOF >/etc/profile.d/locale.sh
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
EOF
    ;;
  *)
    fail "$DISTRO unsupported"
esac

# keyboard: de-latin1-nodeadkeys
echo "Setting keyboard..."
case $DISTRO in
  ubuntu*|debian*)
    case $DISTRO in
      ubuntu_1004)
        PACKAGE="console-setup"
        cat <<EOF >/etc/default/console-setup
VERBOSE_OUTPUT=no
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="Lat15"
FONTFACE="VGA"
FINTSIZE="16"
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT="nodeadkeys"
XKBOPTIONS=""
EOF
        ;;
      *)
        PACKAGE="keyboard-configuration"
        cat <<EOF >/etc/default/keyboard
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT="nodeadkeys"
XKBOPTIONS=""
EOF
        ;;
    esac
    debconf-set-selections <<EOF
debconf $PACKAGE/modelcode string pc105
debconf $PACKAGE/variantcode string nodeadkeys
debconf $PACKAGE/model select Generic 105-key (Intl) PC
debconf $PACKAGE/compose select No compose key
debconf $PACKAGE/layout select Germany
debconf $PACKAGE/layoutcode string de
debconf $PACKAGE/xkb-keymap string de
debconf $PACKAGE/variant select Germany - Eliminate dead keys
debconf $PACKAGE/altgr select The default for the keyboard layout
debconf $PACKAGE/unsupported_layout string true
debconf $PACKAGE/unsupported_config_options string true
EOF
    apt-get install -y $PACKAGE
    dpkg-reconfigure -f noninteractive $PACKAGE
    ;;
  *)
    fail "$DISTRO unsupported"
esac

# SSH keys
echo "Removing SSH keys and adding script for recreation..."
rm -f /etc/ssh/ssh_host_{ecdsa,dsa,rsa}_key{,.pub}
case $DISTRO in
  debian_5|ubuntu*)
    cat <<EOF >/etc/rc2.d/S15ssh_gen_host_keys
#!/bin/bash
ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -N ''
ssh-keygen -f /etc/ssh/ssh_host_dsa_key -t dsa -N ''
ssh-keygen -f /etc/ssh/ssh_host_ecdsa_key -t ecdsa -N ''
rm -f \$0
EOF
    chmod a+x /etc/rc2.d/S15ssh_gen_host_keys
    ;;
  debian_*)
    cat <<EOF >/etc/init.d/ssh_gen_host_keys
#!/bin/sh
### BEGIN INIT INFO
# Provides:          Generates new ssh host keys on first boot
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: Generates new ssh host keys on first boot
# Description:       Generates new ssh host keys on first boot
### END INIT INFO
ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -N ""
ssh-keygen -f /etc/ssh/ssh_host_dsa_key -t dsa -N ""
ssh-keygen -f /etc/ssh/ssh_host_ecdsa_key -t ecdsa -N ""
insserv -r /etc/init.d/ssh_gen_host_keys
rm -f \$0
EOF
    chmod a+x /etc/init.d/ssh_gen_host_keys
    insserv /etc/init.d/ssh_gen_host_keys
    ;;
  *)
    fail "$DISTRO unsupported"
esac

echo "Applying distro-specific changes..."
case $DISTRO in
  ubuntu*)
    echo "Ubuntu: Disabling network wait"
    sed -i -e 's/sleep/#sleep/g' /etc/init/failsafe.conf
    echo "Ubuntu: Disabling boot splash"
    if [ -f /etc/default/grub ]; then
      sed -i -e 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/GRUB_CMDLINE_LINUX_DEFAULT="noplymouth"/g' /etc/default/grub
      update-grub
    fi
    ;;
esac

if [ "$VMTYPE" == "openvz" ]; then
  echo "OpenVZ specific changes..."

  case $DISTRO in
    debian_*)
      sed -i -e '/getty/d' /etc/inittab
      ;;
    ubuntu*)
      #FIXME: disable getty without inittab
      # http://blog.bodhizazen.net/linux/ubuntu-10-04-openvz-templates/
      # https://help.ubuntu.com/community/OpenVZ
      # readlink is needed because newer systems use /run
      cat <<EOF >/etc/init/openvz.conf
# OpenVZ - Fix init sequence to have OpenVZ working with upstart
description "Fix OpenVZ"
start on startup
emits mounting
emits virtual-filesystems
emits local-filesystems
emits remote-filesystems
emits all-swaps
emits filesystem
emits mounted
task
script
do_mount(){
  SRC="\$1"; DST="\$2"; TYPE="\$3"
  mkdir -p \$DST
  initctl emit mounting MOUNTPOINT=\$DST TYPE=\$TYPE --no-wait
  mount -t \$TYPE \$SRC \$DST
  initctl emit mounted MOUNTPOINT=\$DST TYPE=\$TYPE --no-wait
}
dummy_mount(){
  SRC="\$1"; DST="\$2"; TYPE="\$3"
  initctl emit mounting MOUNTPOINT=\$DST TYPE=\$TYPE --no-wait
  initctl emit mounted MOUNTPOINT=\$DST TYPE=\$TYPE --no-wait
}
dummy_mount none /dev tmpfs
do_mount devpts /dev/pts devpts
do_mount varrun $(readlink -m /var/run) tmpfs
do_mount varlock $(readlink -m /var/lock) tmpfs
dummy_mount proc /proc proc
dummy_mount sysfs /sys sysfs
for signal in all-swaps virtual-filesystems local-filesystems remote-filesystems filesystem; do
  initctl emit \$signal --no-wait
done
if [ ! -e /etc/mtab ]; then
  cat /proc/mounts > /etc/mtab
fi
end script
EOF
      # mountall is too smart and detects that / is strange
      echo "manual" > /etc/init/mountall.override
      cat <<EOF >/etc/init.d/openvz
#!/bin/sh
### BEGIN INIT INFO
# Provides:          openvz
# Required-Start:    
# Required-Stop:     
# Default-Start:     1 2 3 4 5
# Default-Stop:      0 6
# Short-Description: OpenVZ Fix
# Description:       Fix for OpenVZ
### END INIT INFO
do_mount(){
  SRC="\$1"; DST="\$2"; TYPE="\$3"
  mkdir -p \$DST
  mount -t \$TYPE \$SRC \$DST
}
case "\$1" in
  start)
    do_mount devpts /dev/pts devpts
    do_mount varrun \$(readlink -m /var/run) tmpfs
    do_mount varlock \$(readlink -m /var/lock) tmpfs
  ;;
esac
EOF
      chmod +x /etc/init.d/openvz
      update-rc.d openvz start 20 1 2 3 4 5 . stop 20 0 6 .
      ;;
    *)
      fail "$DISTRO unsupported"
  esac
  
  # Fix /etc/mtab
  rm -f /etc/mtab
  ln -s /proc/mounts /etc/mtab
fi

echo "Installing nlXTP guest modules..."
case $DISTRO in
  debian*|ubuntu*)
    dpkg -i nlxtp-guest-modules*.deb
    ;;
  *)
    fail "$DISTRO unsupported"
esac
if [ "$VMTYPE" == "kvm" ]; then
  mkdir -p /mnt/nlXTP
  echo "/dev/fd0 /mnt/nlXTP auto defaults,sync,nofail 0 0" >> /etc/fstab
fi

echo "Cleanup..."
case $DISTRO in
  debian*|ubuntu*)
    apt-get clean
    ;;
  *)
    fail "$DISTRO unsupported"
esac

echo
echo "Done. Please reboot VM to use it"
if [ "$VMTYPE" == "openvz" ]; then
  echo "Size inside VM: $(du -shx / | cut -f1)"
fi
