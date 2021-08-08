#include "Motor.h"
#include "Arduino.h"

Motor::Motor(int motorNumber)
{
  motorCommand = "M" + String(motorNumber) + ": ";
  Serial2.begin(9600);
}

void Motor::adjust(double delta)
{
  power = constrain(power + delta, -2048, 2048);
  Serial2.print(motorCommand);
  Serial2.println((int)power);
}

void Motor::set(double setPower)
{
  power = constrain(setPower, -2048, 2048);
  Serial2.print(motorCommand);
  Serial2.println((int)power);
}