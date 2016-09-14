## Template: Debian 8 (KVM)
- Base image: Debian "Jessie" 8.5 amd64
- Variant: Server (non-graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 14.04 (KVM)
- Base image: Ubuntu "Trusty" 14.04.4 amd64
- Variant: Server (non-graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 16.04 (KVM)
- Base image: Ubuntu "Xenial" 16.04.1 amd64
- Variant: Server (non-graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 16.04 Ubuntu-Desktop (KVM)
- Base image: Ubuntu "Xenial" 16.04.1 amd64
- Variant: Ubuntu Desktop (graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 16.04 Lubuntu-Desktop (KVM)
- Base image: Ubuntu "Xenial" 16.04.1 amd64
- Variant: Lubuntu Desktop (graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 16.04 Xubuntu-Desktop (KVM)
- Base image: Ubuntu "Xenial" 16.04.1 amd64
- Variant: Xubuntu Desktop (graphical)
- Build date: 2016-07-22

Changes to default installation:
- Root password: ToMaToRoot
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console/graphically)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Debian 8 (OpenVZ)
- Base image: Debian "Jessie" 8.5
- Variant: Taken directly from Docker (debian:8.5)
- Build date: 2016-08-19

Changes to default installation:
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ryu
- Base image: Debian "Jessie" 8.5
- Variant: Taken directly from Docker (debian:8.5)
- Build date: 2016-08-19

Changes to default installation:
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules
- Ryu 4.3
- Httpie for Rest calls


## Template: Ubuntu 14.04 (OpenVZ)
- Base image: Ubuntu "Trusty" 14.04.4
- Variant: Taken directly from Docker (ubuntu:14.04.4)
- Build date: 2016-08-19

Changes to default installation:
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules


## Template: Ubuntu 16.04 (OpenVZ)
- Base image: Ubuntu "Xenial" 16.04.1
- Variant: Taken directly from Docker (ubuntu:16.04)
- Build date: 2016-08-19

Changes to default installation:
- No user created besides "root"
- Time zone: Europe/Berlin
- All non-essential services deactivated
- SSH is disabled, re-enable it with `ssh-enable`
- Automatic login as root (on console)
- Requiring secure passwords (libpam-pwquality)
- Locale: en_US.UTF-8
- Keyboard: de-latin1-nodeadkeys
- Creating SSH keys on first boot

Additional software:
- Generic utilities: nano, vim-tiny, screen
- Networking utilities: iperf, tcpdump
- nlXTP guest modules

