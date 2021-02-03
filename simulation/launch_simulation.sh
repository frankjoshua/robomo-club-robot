#!/bin/bash

docker stop $(docker ps -aq)
roslaunch simulation.launch &
pid=$!
docker start $(docker ps -aq)
wait "$pid"