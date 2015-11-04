#!/bin/bash

DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
TOMATODIR="$DIR"/../..

function tomato-db-dump () {
  BACKUP_DIR="$DIR"/mongodb-backup
  mkdir -p "$BACKUP_DIR"
  ARCHIVE="$1"
  if [ "$ARCHIVE" == "" ]; then
    ARCHIVE="$DIR/mongodb-dump-$(date +%F).tar.gz"
  fi
  docker run -it --link mongodb:mongo -v "$BACKUP_DIR":/backup --rm mongo sh \
             -c 'mongodump -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" -d tomato --out /backup; chmod -R ogu+rwX /backup'
  tar -czf "$ARCHIVE" -C "$BACKUP_DIR" .
  rm -rf "$BACKUP_DIR"
}

function tomato-db-restore () {
  BACKUP_DIR="$DIR"/mongodb-backup
  rm -rf "$BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
  ARCHIVE="$1"
  if ! [ -f "$ARCHIVE" ]; then
    echo "Archive not found" >&2
    return 1
  fi
  tar -xzf "$ARCHIVE" -C "$BACKUP_DIR"
  docker run -it --link mongodb:mongo -v "$BACKUP_DIR":/backup --rm mongo sh \
             -c 'exec mongorestore -h "$MONGO_PORT_27017_TCP_ADDR:$MONGO_PORT_27017_TCP_PORT" "/backup" --drop'
  rm -rf "$BACKUP_DIR"
}

