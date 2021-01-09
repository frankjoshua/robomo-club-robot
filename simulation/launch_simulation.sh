#!/bin/bash

docker stop $(docker ps -aq)
docker start $(docker ps -aq) &
roslaunch --wait simulation.launch