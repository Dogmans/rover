# UGV02 onboard IMU and encoder telemetry

Vendor documentation and upstream firmware reviewed: 2026-10-12. These are
documented capabilities and source observations, not a live test of the delivered
board. The onboard IMU is part of the hardware baseline; its ROS integration
remains to implement and commission.

## Documented hardware and interface

The [UGV02 manual](https://www.waveshare.com/wiki/UGV02) documents an onboard
9-axis IMU and encoder-equipped drive. Waveshare's
[product hardware description](https://www.waveshare.com/ugv02.htm) identifies
the IMU as ICM-20948. The
[ROS Driver firmware](https://github.com/waveshareteam/ugv_base_ros) also targets
that sensor. Older UGV02 boards use the General Driver firmware; identify the
delivered board and firmware before selecting a parser.

| JSON request | Documented purpose |
| --- | --- |
| `{"T":126}` | Request IMU information |
| `{"T":130}` | Request base feedback |
| `{"T":131,"cmd":1}` | Enable continuous base feedback |

The [firmware command header](https://github.com/waveshareteam/ugv_base_ros/blob/main/ROS_Driver/json_cmd.h)
declares base feedback type `1001` with left/right speed, gyro (`gx/gy/gz`),
acceleration (`ax/ay/az`), magnetic field (`mx/my/mz`), encoder distances
(`odl/odr`) and voltage. It declares a separate IMU feedback type `1002`.
Check actual packets: comments and the shipped implementation may differ.
Defaults for continuous feedback also differ between the UGV02 manual and
upstream source; query/configure behavior deliberately during commissioning.

The [motion implementation](https://github.com/waveshareteam/ugv_base_ros/blob/main/ROS_Driver/movtion_module.h)
computes accumulated left/right wheel travel from encoder counts, wheel diameter
and counts per revolution. These are wheel-distance estimates, not independently
measured ground travel. Scale, direction, turning geometry and slip need calibration.

## Firmware details affecting ROS publication

In the inspected upstream
[main loop](https://github.com/waveshareteam/ugv_base_ros/blob/main/ROS_Driver/ROS_Driver.ino),
gyro and accelerometer variables come from DMP raw fields; the quaternion and
roll/pitch/yaw calculation is commented out. The
[IMU request handler](https://github.com/waveshareteam/ugv_base_ros/blob/main/ROS_Driver/IMU_ctrl.h)
still serializes orientation variables for `T=126`. Their presence does not
establish a valid, updated orientation estimate. This finding concerns inspected
upstream `main`, not proof that every factory firmware has the same behavior.

The future Pi base adapter must establish sensor scaling, axes, bias, update
behavior and timing before publication. ROS
[`sensor_msgs/msg/Imu`](https://github.com/ros2/common_interfaces/blob/jazzy/sensor_msgs/msg/Imu.msg)
requires angular velocity in rad/s and acceleration in m/s^2. Declare unavailable
orientation using its prescribed covariance flag, rather than inventing a valid
identity quaternion. Publish magnetometer data separately if supported/validated.
Keep conversion constants tied to the verified firmware and sensor configuration.

Measure sample freshness and transport delay, including during motor activity.
Do not equate packet-arrival time with acquisition time. If source timing is
unavailable, declare receipt-time stamping and its uncertainty. Record the
delivered firmware identity and observed packet schema before freezing the
driver contract.

## Planned mapping and movement use

Use encoder odometry plus the onboard gyro as the initial short-term motion
estimate on the Pi, with one authoritative odometry/fusion node. Evaluate
`robot_localization` for this role. Let LiDAR SLAM refine map-relative pose and
handle loop closures; Nav2 consumes the resulting map, pose and velocity.
IMU integration does not provide an accurate standalone distance meter.

Start with verified angular velocity for turn estimation; include additional
orientation/acceleration/magnetometer fields only when their quality and frames
are established. Derive covariances from measured behavior. Keep correlated
encoder-derived quantities from being treated as independent observations.

A stop-and-inspect action can check low measured wheel speed and gyro rotation
before admitting an image/scan pair, then check source-time localization and
object-range association. Being stationary helps measurement quality but does
not create depth for an object outside the LiDAR scan plane.

The profile records these sensors under `devices.base.onboard_sensors` because
they share the ESP32 transport. This is inventory metadata, not active driver
configuration. The future base adapter owns that serial connection and publishes
separate ROS IMU and encoder/odometry interfaces. Do not create competing serial
readers or an independent IMU launcher for the same stream.
