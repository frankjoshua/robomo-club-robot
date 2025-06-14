# Robomo.club Robot 2025

Code and documentation for Robomo.club 2019-2025 club robot.

Our website is at [http://robomo.club](http://robomo.club)

The current robot is living at Arch Reactor in St. Louis, MO [http://archreactor.org](http://archreactor.org).

![Club robot](https://robomo.club/d8938d3ade5b99f15ff5d4e3a885581931a0de5a_1_375x500.jpeg)

## Quick start (simulation)

If you just want to see the robot in action without any hardware you can run the
simulation stack on your own computer.

1. Install [Docker](https://docs.docker.com/get-docker/) and
   [Docker Compose](https://docs.docker.com/compose/).
2. Clone this repository and start the containers:

   ```bash
   git clone https://github.com/frankjoshua/robomo-club-robot.git
   cd robomo-club-robot
   ./start_simulation.sh
   ```

   Code Server will be available at [https://localhost:8443](https://localhost:8443) with the password
   `12345678`. Press `Ctrl+C` in the terminal to stop the simulation.

   n8n will be available at [https://localhost:5678](https://localhost:5678)

Continue with the steps below if you want to install the software on a real
robot.

# Getting started

These instructions assume you are installing from a linux computer. And that you are on the same network as your robot.

### Prerequisites

- [Ansible](https://docs.ansible.com/) installed on your workstation
- Ability to `ssh` into the robot as the `robot` user

Ansible is used to install and update software on the robot. The `ansible`
directory contains the playbooks and configuration files:
/ansible/production --> Hostname and IP address of the robot
/ansible/robot.yml --> Playbook for robot software
/ansible/ssh.yml --> Installs ssh keys for user "robomo"
/ansible/files/ssh_keys --> Public and private keys for user "robomo"

Run this command to install or update the robot
```
cd ansible
ansible-playbook -i production ssh.yml -Kk
ansible-playbook -i production robot.yml
```

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

Then you should be able to ssh into the nano with out a password and run sudo commands. If not fix it.

```
ssh robot
```

# Simulating the robot

The simulation containers can be launched using docker compose.

```bash
./start_simulation.sh
```
![sim](images/sim.svg)

# Contributors:

Mark Moran<br>
Joshua Frank
