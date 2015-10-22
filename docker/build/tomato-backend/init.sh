#!/bin/bash

if ! [ -f /etc/tomato/backend.pem ]; then
  openssl req -new -x509 -days 1000 -nodes -out /etc/tomato/backend.pem -keyout /etc/tomato/backend.pem -subj /CN=`hostname`/ -batch
fi

if ! [ -f /etc/tomato/server.cert ]; then
  openssl req -new -x509 -days 1000 -nodes -out /etc/tomato/server.cert -keyout /etc/tomato/server.cert -subj /CN=`hostname`/ -batch
fi

if ! [ -d /data/templates ]; then
  mkdir -p /data/templates
fi

echo "$TIMEZONE" > /etc/timezone
cp "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime