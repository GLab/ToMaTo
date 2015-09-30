#!/bin/bash

rsync -Pav repository/ root@packages.tomato-lab.org:/var/www/packages/
