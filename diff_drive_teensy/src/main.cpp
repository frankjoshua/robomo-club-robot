#include <Arduino.h>
#include "Motor.h"
#include "Kinematics.h"

#include <ros.h>
#include "geometry_msgs/Twist.h"

#define MAX_RPM 330             // motor's maximum RPM
#define WHEEL_DIAMETER 0.15     // wheel's diameter in meters
#define LR_WHEELS_DISTANCE 0.35 // distance between left and right wheels
#define FR_WHEELS_DISTANCE 0.30 // distance between front and rear wheels.

Motor leftMotor(2);
Motor rightMotor(1);
Kinematics kinematics(Kinematics::DIFFERENTIAL_DRIVE, MAX_RPM, WHEEL_DIAMETER, FR_WHEELS_DISTANCE, LR_WHEELS_DISTANCE);

void cmdVelCallback(const geometry_msgs::Twist &cmd_msg);

ros::Subscriber<geometry_msgs::Twist> cmd_sub("cmd_vel", cmdVelCallback);
ros::NodeHandle nh;

long lastCommandTime = 0;

Kinematics::rpm goalRPM;
void cmdVelCallback(const geometry_msgs::Twist &cmd_msg)
{
  //callback function every time linear and angular speed is received from 'cmd_vel' topic
  //this callback function receives cmd_msg object where linear and angular speed are stored
  lastCommandTime = millis();
  goalRPM = kinematics.getRPM(cmd_msg.linear.x, cmd_msg.linear.y, cmd_msg.angular.z);
  // Serial.println(goalRPM.motor1);
  // Serial.println(goalRPM.motor2);
}

void setup()
{
  Serial.begin(115200);

  //Setup ROS
  nh.initNode();
  nh.subscribe(cmd_sub);
  while (!nh.connected())
  {
    nh.spinOnce();
  }
}

void loop()
{
  delay(10);
  nh.spinOnce();

  if (millis() - lastCommandTime > 400)
  {
    goalRPM = kinematics.getRPM(0, 0, 0);
  }

  int leftPower = map(goalRPM.motor1, -MAX_RPM, MAX_RPM, -2048, 2048);
  int rightPower = map(goalRPM.motor2, -MAX_RPM, MAX_RPM, -2048, 2048);
  leftMotor.set(leftPower);
  rightMotor.set(rightPower);
}