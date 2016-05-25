#!/bin/bash
cd "$(dirname "$0")"

if [ -d "$1" ]; then
	python -m unittest discover -v -s "$1" -p "*_test.py"
else
	echo "usage: $0 [TOMATO_MODULE]"
fi
