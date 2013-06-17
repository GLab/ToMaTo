#!/bin/bash

#
# requires packages
#
# dh-make debuild devscripts
#

cd $(dirname $0)
cd nlxtp-guest-modules-0.1
debuild -us -uc
