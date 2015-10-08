#!/bin/bash
pushd $(dirname $0)
python convert.py "$@"
popd
