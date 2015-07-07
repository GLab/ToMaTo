#!/bin/bash

set -e

FILE="$1"
# 1) try to extract "#TAG ..."
if [ $(sed -n '/^#TAG[ \t]\+\(.*\)[ \t]*$/Is//\1/p' "$FILE" | wc -l) == 1 ]; then
  sed -n '/^#TAG[ \t]\+\(.*\)[ \t]*$/Is//\1/p' "$FILE"
  exit 0
fi
# 2) try to extract "ENV *VERSION ..."
if [ $(sed -n '/^[ \t]*ENV[ \t]\+[a-zA-Z_]*VERSION[ \t]\+\(.*\)[ \t]*$/Is//\1/p' "$FILE" | wc -l) == 1 ]; then
  sed -n '/^[ \t]*ENV[ \t]\+[a-zA-Z_]*VERSION[ \t]\+\(.*\)[ \t]*$/Is//\1/p' "$FILE"
  exit 0
fi
# 3) use the current date
date +%F
