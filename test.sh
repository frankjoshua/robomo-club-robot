#!/bin/bash

cd ./tests
vagrant up
cd ..
./install.sh --limit vagrant
cd ./tests
./run_tests.sh