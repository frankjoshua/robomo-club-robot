# Teleop diagnostics, September 12, 2026

After USB reconnection the owner still reported no movement from ROS2y. A fresh
listener inside the micro-ROS agent container received ten small decreasing
/cmd_vel values followed by zero, delivered in a burst during discovery. It
received 787 wheel messages over 40 seconds, all with zero velocity and power.
There was no sustained new input during the rest of that observation window.
This does not prove whether the Teensy consumed the captured transient commands.

Two bounded physical tests then used driver.sh laser-check, the normal closed-loop
/cmd_vel path, laser/depth clearance guards, a 0.06 m/s ceiling, 1.5-second duration,
and 0.08 m travel limit. Nav2 was stopped to prevent competing goals.

| Test origin and middleware | Observed travel | Maximum left/right power | Final wheels |
| --- | --- | --- | --- |
| TX2, Fast DDS | 0.0697 m | 0.276 / 0.251 | velocity and power zero |
| TX2, Cyclone DDS | 0.0703 m | 0.238 / 0.240 | velocity and power zero |

Both completed without a guard failure; both wheel encoders registered movement.
Records are teleop-local-move.json and teleop-cyclone-local-move.json under
/home/operator/calibration-tests/20260912 on TX2. This confirms the local motor
command paths work with both middleware implementations.

The same guarded test from the laptop ROS2y container aborted before movement:
no depth clouds arrived. It received laser, odometry, wheel and IMU data. Local
record: /tmp/calibration-20260912/teleop-laptop-move.json. This test does not prove
that a laptop velocity command fails; the clearance guard correctly refused
motion without depth. Nav2 was restarted after these tests.

The owner was asked whether pressing W changes ROS2y's sidebar to teleop ACTIVE
with a nonzero cmd value. That distinction remains needed to separate UI input
handling from sustained command delivery. Do not claim ROS2y teleop is repaired
based on publisher discovery or the two successful robot-local moves.

The driver accepts RMW_IMPLEMENTATION for its guarded test and can use an existing
ROS_DIAGNOSTIC_CONTAINER with CYCLONEDDS_URI for the same guarded client-side test.

## Confirmed ROS2y recovery

The owner confirmed the sidebar reported ACTIVE and a positive command.
A bounded 0.2-second W input followed by X was then injected through driver.sh
into the verified running ROS2y terminal, after fresh robot-side clearance
checks and with Nav2 stopped. Simultaneous listeners showed six command messages
on the laptop and none on the robot; wheel power and speed remained zero.
Thus the UI handled the input, but its commands were not delivered to the TX2.

The micro-ROS agent now selects `ROBOT_MICRO_ROS_DDS_PROFILE` in hardware Compose.
On this TX2, `.env` sets it to `./config/tx2-fastdds-lan.xml`, which advertises
192.168.8.230 and local loopback, excluding Tailscale. Other Fast DDS containers
retain their existing profile. Recreating only the agent restored its session
without another Teensy USB reboot.

With the original ROS2y process still running, the exact same bounded key test
then delivered all six command messages to a listener in the agent container,
spaced at about 50 ms. Both wheel encoders registered movement (peaks 0.369 and
0.372 rad/s), motor effort rose, and X returned both speeds and efforts to zero.
Evidence: ui-lan-agent-trace.jsonl, compared with ui-laptop-trace.jsonl and
ui-robot-trace.jsonl in the calibration directory. This is actual ROS2y command
and wheel-response verification, not just DDS graph discovery.

This establishes recovery after the profile change and agent recreation. It
does not isolate a particular upstream DDS bug or prove which locator caused
the failed delivery. Packet inspection also found discovery traffic to obsolete
192.168.2.x addresses; that traffic was not established to be motor commands.
Navigation was restored after testing. No motor gains, geometry or obstacle
thresholds were changed by this repair.

The first LAN-only trial restored teleop but interrupted the existing Fast DDS
odometry and diagnostics subscribers. Adding loopback back to the agent's
profile restored these TX2-local consumers while retaining the teleop fix.
The final profile therefore includes 127.0.0.1 and 192.168.8.230, not Tailscale.
A coordinated recording and W/X test then verified six received commands,
left/right peak wheel speeds 0.357/0.335 rad/s, and final wheel speed and power
zero. This final evidence is ui-final-agent-trace.jsonl. Both odometry and
Teensy diagnostics recovered without restarting the odometry process or resetting
its pose. Source-count diagnostics settled back to one source per input.
