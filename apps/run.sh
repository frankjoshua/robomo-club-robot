#!/bin/bash

docker run --rm -v "$(pwd):/app" -w /app frankjoshua/ros2-nav2 bash -c "python3 $@"