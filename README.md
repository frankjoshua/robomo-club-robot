# robomo-club-robot
Code and documentation for Robomo.club 2019 club robot

For more information on our project check out our formum at https://discourse.robomo.club/t/robomo-club-robot-project/82

To see the todo list follow this link. https://github.com/frankjoshua/robomo-club-robot/projects/1

Our website is at http://robomo.club

# Getting started
Ansible is used to install and update software on the robot. You must have it installed on your workstation and be able to ssh into the robot from your worksation before continuing.
/ansible/prduction = Has hostname and ip address of the robot
/ansible/robot.yml = Playbook for robot software

Run this command to install or update the robot
cd ansible
ansible-playbook -i ./production robot.yml -Kk

# Contributors:
Mark Moran
Joshua Frank