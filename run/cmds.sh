#!/bin/bash

DIR=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))

function tomato-db-start () {
  docker run -d -v "$DIR"/mongodb-data:/data/db -p 127.0.0.1:27017:27017 --name mongodb mongo
  docker start mongodb
}

function tomato-backend-start () {
  docker run -d -v "$DIR"/../backend:/code -v "$DIR"/../shared:/shared -v "$DIR"/backend/config:/config -v "$DIR"/backend/data:/data -v "$DIR"/backend/logs:/logs --link mongodb:db -p 8006:8006 -p 8000:8000 -p 8001:8001 -p 8002:8002 --name tomato-backend tomato-backend
  docker start tomato-backend
}

function tomato-db-stop () {
  docker stop mongodb
  docker rm mongodb
}

function tomato-backend-stop () {
  docker stop tomato-backend
  docker rm tomato-backend 
}

function tomato-start () {
  tomato-db-start
  tomato-backend-start
}

function tomato-stop () {
  tomato-backend-stop
  tomato-db-stop
}

function tomato-restart() {
  tomato-stop
  tomato-start
}
