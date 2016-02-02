#/bin/bash

set -e

NAME="$1"
shift
ARGS="$@"
VERSION=$(./getversion.sh "$NAME/Dockerfile")
docker build --rm $ARGS -t "$NAME:$VERSION" "$NAME"
docker tag -f "$NAME:$VERSION" "$NAME:latest"
