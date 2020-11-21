## Robomo Club Robot simulation

# Requirments

Assumes a linux based system.<br>
Requires Vagrant and VirtualBox to be installed.<br>
30GB Free space<br>

```
vagrant plugin install vagrant-disksize
```

# Running

Launch the VM. This will take a long time when first run. It has to download the OS and configure ROS.

```
./start.sh
```

Then open the VM and login with the username/password of vagrant/vagrant.<br>

Launch Gazebo with:

```
cd /vagrant
roslaunch --wait ./simulation.launch
```

# SSH Setup

It makes everything better if you setup your ssh config in ~/.ssh/config
You can output the ssh config with `vagrant ssh-config`. Copy that into ~/.ssh/config and edit the host so it is "robot". Mine looked like this:

```
Host robot
  HostName 127.0.0.1
  User vagrant
  Port 2222
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/josh/development/workspace/robomo-club-robot/simulation/.v$
  IdentitiesOnly yes
  LogLevel FATAL
```

After that you should be able to ssh into the VirtualBox with:

```
ssh robot
```

# Install Robot Software on Simulation

Once ssh is setup just install as normal. Gazebo needs to be running before you start the other ROS nodes. When Gazebo starts it sets /use_sim

```
./install.sh
```
