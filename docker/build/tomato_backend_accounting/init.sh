#!/bin/bash

echo "$TIMEZONE" > /etc/timezone
cp "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime
