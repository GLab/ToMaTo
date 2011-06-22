#!/bin/bash
for package in backend web cli; do
	(cd $package/tomato-$package; dch --distribution stable --force-distribution "$@")
done
