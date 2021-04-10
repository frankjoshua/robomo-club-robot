#!/bin/bash

docker start $(docker stop $(docker ps -aq))
