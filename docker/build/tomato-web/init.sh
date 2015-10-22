#!/bin/bash

if [ -f /etc/tomato/web.conf ]; then
  sed -i -e "s/XXX_REPLACE_ME_XXX/$(cat /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c33)/g" /etc/tomato/web.conf
fi

if ! [ -f /etc/tomato/web.pem ]; then
  openssl req -new -x509 -days 1000 -nodes -out /etc/tomato/web.pem -keyout /etc/tomato/web.pem -subj /CN=`hostname`/ -batch
fi

echo "$TIMEZONE" > /etc/timezone
cp "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime