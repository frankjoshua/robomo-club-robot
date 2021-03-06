#!/bin/bash

docker stop $(docker ps -aq)
roslaunch simulation.launch &
pid=$!
docker start $(docker ps -aq)
## Stop ros master because the simulation is running ros master
docker stop ros_master
wait "$pid"