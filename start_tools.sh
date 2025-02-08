#!/bin/bash

export PUID=$(id -u)
export PGID=$(id -g)
docker-compose -f docker-compose-tools.yml up -d

