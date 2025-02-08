#!/bin/bash

docker run --rm -it -v "$(pwd):/app" -w /app --network="host" --pid="host" --ipc="host" frankjoshua/ros2-nav2 bash