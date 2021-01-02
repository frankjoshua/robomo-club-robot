#!/bin/bash

docker stop $(docker ps -aq)
roslaunch --wait simulation.launch &
docker start $(docker ps -aq)