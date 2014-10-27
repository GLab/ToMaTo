#!/bin/bash

c_rehash /etc/tomato/client_certs
cat /etc/tomato/client_certs/*.pem > /etc/tomato/client_certs.pem
