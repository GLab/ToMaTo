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
if lspci -v | fgrep -q Qemu; then
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
    apt-get install -y ssh nano iperf tcpdump screen vim-tiny locales manpages man-db less
    ;;
  *)
    fail "$DISTRO unsupported"
esac


echo "Disabling services..."
case $DISTRO in
  ubuntu*)
    service ssh stop
    update-rc.d -f ssh remove
    echo "manual" > /etc/init/ssh.override
    cat <<EOF >/usr/local/bin/ssh-enable
#!/bin/bash
set -e
echo "Please select a secure root password"
passwd root
rm /etc/init/mountall.override
service ssh start
EOF
    chmod +x /usr/local/bin/ssh-enable
    ;;
  debian*)
    /etc/init.d/ssh stop
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
    apt-get install -y mingetty
    sed -i -e 's/\/sbin\/getty 38400/\/sbin\/mingetty --autologin root --noclear/g' /etc/inittab
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
    cat <<EOF >/etc/default/keyboard
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT="nodeadkeys"
XKBOPTIONS=""
EOF
    debconf-set-selections <<EOF
debconf keyboard-configuration/modelcode string pc105
debconf keyboard-configuration/variantcode string nodeadkeys
debconf keyboard-configuration/model select Generic 105-key (Intl) PC
debconf keyboard-configuration/compose select No compose key
debconf keyboard-configuration/layout select Germany
debconf keyboard-configuration/layoutcode string de
debconf keyboard-configuration/xkb-keymap string de
debconf keyboard-configuration/variant select Germany - Eliminate dead keys
debconf keyboard-configuration/altgr select The default for the keyboard layout
debconf keyboard-configuration/unsupported_layout string true
debconf keyboard-configuration/unsupported_config_options string true
EOF
    dpkg-reconfigure -f noninteractive keyboard-configuration
    ;;
  *)
    fail "$DISTRO unsupported"
esac

# SSH keys
echo "Removing SSH keys and adding script for recreation..."
rm -f /etc/ssh/ssh_host_{dsa,rsa}_key{,.pub}
case $DISTRO in
  debian_5|ubuntu*)
    cat <<EOF >/etc/rc2.d/S15ssh_gen_host_keys
#!/bin/bash
ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -N ''
ssh-keygen -f /etc/ssh/ssh_host_dsa_key -t dsa -N ''
rm -f \$0
EOF
    chmod a+x /etc/rc2.d/S15ssh_gen_host_keys
    ;;
  debian_6)
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
insserv -r /etc/init.d/ssh_gen_host_keys
rm -f \$0
EOF
    chmod a+x /etc/init.d/ssh_gen_host_keys
    insserv /etc/init.d/ssh_gen_host_keys
    ;;
  *)
    fail "$DISTRO unsupported"
esac


if [ "$VMTYPE" == "openvz" ]; then
  echo "OpenVZ specific changes..."

  case $DISTRO in
    debian*)
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
      ;;
    *)
      fail "$DISTRO unsupported"
  esac
  
  # Fix /etc/mtab
  rm -f /etc/mtab
  ln -s /proc/mounts /etc/mtab
fi

echo "Cleanup..."
case $DISTRO in
  debian*|ubuntu*)
    apt-get --purge clean
    ;;
  *)
    fail "$DISTRO unsupported"
esac

echo
echo "Done. Please reboot VM to use it"
echo "Size inside VM: $(du -shx / | cut -f1)"