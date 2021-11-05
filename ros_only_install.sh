#!/bin/bash

ansible-playbook -i ./ansible/production ./ansible/ros.yml $@