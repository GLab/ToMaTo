#!/bin/bash

DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
TOMATODIR="$DIR"/../..

function tomato-db-start () {
  mkdir -p "$DIR"/mongodb-data
  docker run -d -v "$DIR"/mongodb-data:/data/db -p 127.0.0.1:27017:27017 --name mongodb mongo
  docker start mongodb
}

function tomato-backend-start () {
  mkdir -p "$DIR"/backend/{config,data,logs}
  docker run -d -v "$TOMATODIR"/backend:/code -v "$TOMATODIR"/shared:/shared -v "$DIR"/backend/config:/config -v "$DIR"/backend/data:/data -v "$DIR"/backend/logs:/logs --link mongodb:db -p 8006:8006 -p 8000:8000 -p 8001:8001 -p 8002:8002 --name tomato-backend tomato-backend
  docker start tomato-backend
}

function tomato-web-start () {
  mkdir -p "$DIR"/web/config
  SECRET_KEY=$(cat /dev/urandom | tr -cd 'a-zA-Z0-9' | head -c 32)
  docker run -d -v "$TOMATODIR"/web:/code -v "$TOMATODIR"/shared:/shared -v "$DIR"/web/config:/config --link tomato-backend:backend -p 8080:80 --name tomato-web -e "SECRET_KEY=$SECRET_KEY" tomato-web
  docker start tomato-web
}

function tomato-db-stop () {
  docker stop mongodb
  docker rm mongodb
}

function tomato-backend-stop () {
  docker stop tomato-backend
  docker rm tomato-backend
}

function tomato-web-stop () {
  docker stop tomato-web
  docker rm tomato-web
}

function tomato-backend-restart() {
  tomato-web-stop
  tomato-backend-stop
  tomato-backend-start
  tomato-web-start
}

function tomato-web-restart() {
  tomato-web-stop
  tomato-web-start
}

function tomato-start () {
  tomato-db-start
  tomato-backend-start
  tomato-web-start
}

function tomato-stop () {
  tomato-web-stop
  tomato-backend-stop
  tomato-db-stop
}

function tomato-restart() {
  tomato-stop
  tomato-start
}
