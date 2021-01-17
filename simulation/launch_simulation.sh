#!/bin/bash

docker stop $(docker ps -aq)
roslaunch simulation.launch &
docker start $(docker ps -aq)