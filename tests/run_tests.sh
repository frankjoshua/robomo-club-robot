#!/bin/bash

vagrant ssh-config > .vagrant/ssh-config
py.test --hosts=default --ssh-config=.vagrant/ssh-config