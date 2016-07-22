#!/bin/bash

#Basis: fully upgraded debian based system
# aptitude update; aptitude -yR dist-upgrade

set -e; trap 'archive_setstatus "ERROR: Script failed"' ERR

if ! ping -c 1 www.google.com >/dev/null 2>&1; then
  archive_setstatus "ERROR: Not Internet connection"
  exit 1
fi

archive_setstatus "Installing python..."
aptitude -yR install python

archive_setstatus "Installing httpie..."
aptitude -yR install httpie

archive_setstatus "Installing pip..."
aptitude -yR install python-pip

archive_setstatus "Installing ryu dependencies..."
aptitude -yR install python-lxml python-greenlet python-paramiko python-eventlet python-routes python-webob python-netaddr
pip install --upgrade netaddr

archive_setstatus "Installing ryu..."
pip install ryu

archive_setstatus "Preparing template..."
./prepare_vm.sh

archive_setstatus "Done."
