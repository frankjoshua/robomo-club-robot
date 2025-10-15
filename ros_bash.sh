#!/bin/bash
xhost +
docker run --rm -it \
  -v "$(pwd):/app" \
  -w /app \
  --network="host" \
  --pid="host" \
  --ipc="host" \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  ghcr.io/sloretz/ros:jazzy-desktop-full bash

