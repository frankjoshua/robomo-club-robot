# Robomo Club Robot simulation

## Requirements

Assumes a linux based system.<br>
Requires Vagrant and VirtualBox to be installed.<br>
30GB Free space<br>

```
vagrant plugin install vagrant-disksize
```

## Running the Virtual Machine

Launch the VM. This will take a long time when first run. It has to download the OS and configure ROS.

```
./start.sh
```

The first time after running start.sh you will need to reboot the vm to start the GUI.

```
vagrant halt
vagrant up
```

## SSH Setup

It makes everything easier if you setup your ssh config in ~/.ssh/config.
You can output the ssh config with `vagrant ssh-config`. Copy that into ~/.ssh/config and edit the host so it is "robot". Mine looked like this after I was done:

```
Host robot
  HostName 127.0.0.1
  User vagrant
  Port 2222
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/josh/development/workspace/robomo-club-robot/simulation/.vagrant/machines/workstation/virtualbox/private_key
  IdentitiesOnly yes
  LogLevel FATAL
```

After that you should be able to ssh into the VirtualBox with:

```
ssh robot
```

## Start the Simulation

Open the VM and login with the username/password of vagrant/vagrant.<br>

Launch Gazebo with:

```
cd /vagrant
roslaunch --wait ./simulation.launch
```

You should see this output:<br>
roscore/master is not yet running, will wait for it to start
<br>
After the ROS master is installed it should continue. Just move on to the next section for now.

## Install Robot Software on Simulation

Once ssh is setup just install as normal. Gazebo needs to be running before you start the other ROS nodes. When Gazebo starts it sets /use_sim

```
./install.sh
```
