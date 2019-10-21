#!/bin/bash

# vagrant ssh-config > .vagrant/ssh-config
py.test -qq --nagios --tb line --hosts=default --ssh-config=.vagrant/ssh-config