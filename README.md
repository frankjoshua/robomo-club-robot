# robomo-club-robot

Code and documentation for Robomo.club 2019 club robot

For more information on our project check out our forum at https://discourse.robomo.club/t/robomo-club-robot-project/82

To see the todo list follow this link. https://github.com/frankjoshua/robomo-club-robot/projects/1

Our website is at http://robomo.club

# Getting started

Ansible is used to install and update software on the robot. You must have it installed on your workstation and be able to ssh into the robot from your workstation before continuing.
/ansible/production --> Has hostname and ip address of the robot
/ansible/robot.yml --> Playbook for robot software
/ansible/ssh.yml --> Installs ssh keys for user "operator"
/ansible/files/ssh_keys --> Public and private keys for user "operator"

Run this command to install or update the robot
cd ansible
ansible-playbook -i production ssh.yml -Kk
ansible-playbook -i production robot.yml

# SSH setup

`cp ./ansible/files/ssh_keys/robot_id_rsa ~/.ssh/`

Then edit the file ~/.ssh/config (create if it doesn't exist).
Add the following lines to the file replacing <IP_OF_JETSON_NANO> with the address of the Jetson nano

```
Host robot
HostName <IP_OF_JETSON_NANO>
User operator
IdentityFile ~/.ssh/robot_id_rsa
```

Then you should be able to ssh into the nano with

`ssh robot`

# Running Tests

Testing uses Ansible, Vagrant and Infraspec.

You can setup your workstation using:
ansible-playbook -i production testing_server.yml

Then run:

```
./test.sh
```

# Links

[https://www.dimensionengineering.com/datasheets/KangarooManual.pdf](https://www.dimensionengineering.com/datasheets/KangarooManual.pdf)

# Contributors:

Mark Moran<br>
Joshua Frank
