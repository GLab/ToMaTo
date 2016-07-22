#!/bin/bash

function step() {
  desc="$1"
  shift
  archive_setstatus "$desc..."
  if ! "$@"; then
    archive_setstatus "$desc failed"
    exit 1
  fi
}

step "Updating package database" aptitude update
step "Installing java" aptitude install -Ry default-jre-headless
step "Installing python and curl" aptitude install -Ry python curl
step "Cleaning up packages" rm -f /var/cache/apt/archives/*.deb

function install_floodlight() {
  set -e
  mkdir -p /usr/local/lib/floodlight
  cp $archive_dir/floodlight.jar /usr/local/lib/floodlight/floodlight.jar
  cp $archive_dir/floodlightdefault.properties /etc/floodlight.conf
  cp $archive_dir/floodlight.initd /etc/init.d/floodlight 
  chmod +x /etc/init.d/floodlight 
  update-rc.d floodlight defaults
  mkdir -p /usr/local/lib/floodlight/apps
  cp $archive_dir/circuitpusher.py /usr/local/lib/floodlight/apps/circuitpusher.py
  cp $archive_dir/circuitpusher.sh /usr/local/bin/circuitpusher
  chmod +x /usr/local/bin/circuitpusher
  set +e
}

step "Installing floodlight daemon" install_floodlight
archive_setstatus "Finished"