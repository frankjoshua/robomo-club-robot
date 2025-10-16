#!/bin/bash
xhost +local:root

docker run --rm -it \
  --env="DISPLAY=$DISPLAY" \
  --env="QT_X11_NO_MITSHM=1" \
  --env="LIBGL_ALWAYS_SOFTWARE=1" \
  --env="MESA_GL_VERSION_OVERRIDE=3.3" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "$(pwd):/app" \
  -w /app \
  --network=host \
  ghcr.io/sloretz/ros:jazzy-desktop-full \
  bash
