# Robomo.club Robot 2021

Code and documentation for Robomo.club 2019-2021 club robot.

The current robot is living at Arch Reactor in St. Louis, MO (http://archreactor.org).

For more information on our project check out our forum at https://discourse.robomo.club/t/robomo-club-robot-project/82

To see the todo list follow this link. https://github.com/frankjoshua/robomo-club-robot/projects/1

Our website is at http://robomo.club

# Getting started

These instructions assume you are installing from a linux computer. And that you are on the same network as your robot.

Ansible is used to install and update software on the robot. You must have it installed on your workstation and be able to ssh into the robot from your workstation before continuing.
/ansible/production --> Has hostname and ip address of the robot
/ansible/robot.yml --> Playbook for robot software
/ansible/ssh.yml --> Installs ssh keys for user "robot"
/ansible/files/ssh_keys --> Public and private keys for user "robot"

Run this command to install or update the robot
cd ansible
ansible-playbook -i production ssh.yml -Kk
ansible-playbook -i production robot.yml

# SSH setup (Assuming you are working from a Linux computer)

**\*Do not follow these instructions if your robot is in production or is accessible from the internet. This is for convenience in a shared project.**

First copy the ssh key and fix the file permissions.

```
cp ./ansible/files/ssh_keys/robot_id_rsa ~/.ssh/
chmod 400 ~/.ssh/robot_id_rsa
```

Then edit the file ~/.ssh/config (create if it doesn't exist).
Add the following lines to the file replacing <IP_OF_JETSON_NANO> with the address of the Jetson nano or whatever computer you use. Or use 127.0.0.1 if you are installing on the local system.

```
Host robot
HostName <IP_OF_JETSON_NANO>
User robot
IdentityFile ~/.ssh/robot_id_rsa
```

Then you should be able to ssh into the nano with. If not fix it.

```
ssh robot
```

# Running Tests

Testing uses Ansible, Vagrant and Infraspec.

You can setup your workstation using:
ansible-playbook -i production testing_server.yml

Then run:

```
./test.sh
```

# Simulating the robot

```bash
docker run -it \
    --network="host" \
    frankjoshua/ros2-bridge-suite
```

```bash
docker run -it \
    --network="host" \
    frankjoshua/ros2-diff-drive-controller
```

```bash
docker run -it \
    --network="host" \
    frankjoshua/ros2-urdf
```

# Links

[https://www.dimensionengineering.com/datasheets/KangarooManual.pdf](https://www.dimensionengineering.com/datasheets/KangarooManual.pdf)

# Contributors:

Mark Moran<br>
Joshua Frank
