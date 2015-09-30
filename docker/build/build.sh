#/bin/bash

set -e

NAME="$1"
VERSION=$(./getversion.sh "$NAME/Dockerfile")
docker build --rm -t "$NAME:$VERSION" "$NAME"
docker tag -f "$NAME:$VERSION" "$NAME:latest"
