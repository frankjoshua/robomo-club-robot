#!/bin/bash

#Install Ansible Roles
ansible-galaxy install -r ./ansible/requirements.yml
#Run playbook to install softare on the Robot
ansible-galaxy role install -f -r ./ansible/requirements.yml
ansible-galaxy collection install -f -r ./ansible/requirements.yml
ansible-playbook -i ./ansible/production ./ansible/ssh.yml
ansible-playbook -i ./ansible/production ./ansible/all.yml $@