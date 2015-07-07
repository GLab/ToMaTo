#!/bin/bash

if ! [ -f /etc/tomato/backend.pem ]; then
  openssl req -new -x509 -days 1000 -nodes -out /etc/tomato/backend.pem -keyout /etc/tomato/backend.pem -subj /O=`hostname`/ -batch
fi

if ! [ -f /etc/tomato/server.cert ]; then
  openssl req -new -x509 -days 1000 -nodes -out /etc/tomato/server.cert -keyout /etc/tomato/server.cert -subj /O=`hostname`/ -batch
fi

if ! [ -d /data/templates ]; then
  mkdir -p /data/templates
fi
