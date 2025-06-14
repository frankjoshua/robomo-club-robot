#!/bin/bash

# Start tooling containers in the background
export PUID=$(id -u)
export PGID=$(id -g)
docker compose -f docker-compose-tools.yml up -d

# Start ROS containers required for simulation
docker compose -f docker-compose-ros.yml up -d

# Launch the simulation stack in the foreground
xhost +local:docker # Allow local docker to connect to X server for Gazebo
docker compose -f docker-compose-simulation.yml up
