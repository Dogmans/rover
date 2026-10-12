# Pi installation and hardware commissioning guide

Reviewed: 2026-10-12. This document owns procedures for the current Pi deployment
and new hardware bring-up. Use [Feature status](../project/FEATURE_STATUS.md) for
what has passed, and the [architecture](../architecture/ROS_ARCHITECTURE.md) for
component ownership and planned interfaces. Dated measurements and package
versions are preserved in the [11 October commissioning record](../archive/COMMISSIONING_2026-10-11.md).

## Choose the procedure you need

| Situation | Start here |
| --- | --- |
| Existing commissioned Pi; apply repository service/profile updates | [Deploy the camera services](#deploy-the-camera-services-on-the-commissioned-pi) |
| Blank/new Pi installation | [Fresh Pi prerequisites](#fresh-pi-prerequisites), then camera acceptance and service deployment |
| First ESP32/base integration | [Commission the base](#commission-the-esp32-base) |
| LD06 or replacement sensor | [Commission LiDAR](#commission-lidar-and-local-navigation-inputs) |
| Run the current Windows viewer | [PC viewer guide](../../tools/pc/README.md) |

The current Pi has passed Ubuntu Server 24.04 ARM64, ROS 2 Jazzy, CSI still/video
capture and ROS image/CameraInfo publication. Camera calibration and the updated
profile-driven service deployment remain acceptance work. A fresh installation
must repeat the capture/publication gate; the existing evidence does not certify
another image or package combination.

## Connect to the Pi

Copy [`pi.sshconfig.example`](../../pi.sshconfig.example) to the ignored
`pi.sshconfig.local`, set the host/user for your machine, and configure public-key
SSH. Run from the repository root on the PC:

```powershell
ssh -F .\pi.sshconfig.local rover-pi
```

The following shell commands run on the Pi unless labelled otherwise. The current
service units target user `barry`, ROS domain `20`, and localhost-only discovery.
Adapt the units and workspace paths deliberately for a different installation;
exporting a shell variable alone does not change a systemd service environment.

## Fresh Pi prerequisites

1. Prepare Ubuntu Server 24.04 LTS 64-bit ARM with Raspberry Pi Imager, configuring
   the intended hostname, networking, user and SSH. Keep a separate rated Pi
   bench supply; the chassis board's Pi power budget is still unqualified.
2. Boot, verify SSH and update Ubuntu. Record image/kernel/package versions.
3. Install ROS 2 Jazzy base and the build tools needed for the chosen camera
   workspace using the official distribution instructions. Source the ROS setup
   file in shells used for ROS inspection.
4. Establish a Pi 5/IMX708-compatible libcamera/rpicam stack and build/install a
   matching `camera_ros`. The commissioned Pi required Raspberry Pi's PiSP-capable
   libcamera and a source-built camera workspace; Ubuntu's packaged versions were
   not sufficient for that combination. Use the archived version/compatibility
   evidence as a reference, not an assurance that arbitrary newer packages match.
5. Clone this repository on the Pi with both `deploy/pi` and `config/hardware`.
   Keep the camera workspace separate from the checkout.

The exact camera source-build commands and local compatibility patch were not
captured as a reproducible installer. Reconstructing/recording them is a remaining
fresh-install reproducibility task; `install-visualization.sh` assumes a working
ROS/camera workspace and does not install those prerequisites.

Waveshare's full `ugv_rpi` host installer is not part of this procedure. Its code
is a protocol/deployment reference. Keep factory ESP32 firmware initially; select
the matching firmware source after identifying the delivered board.

## Verify local camera capture and ROS publication

First confirm the camera through the supported libcamera pipeline, capture a
still and a short video with the installed utilities, and inspect real frames.
A V4L2 device listing alone is not end-to-end Pi 5 CSI acceptance. The archived
record describes the working PiSP path and the failed packaged-library attempt.

Then, on the commissioned Pi or an equivalently prepared workspace:

```bash
source /opt/ros/jazzy/setup.bash
source /home/barry/camera_ws/install/setup.bash
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:${LD_LIBRARY_PATH:-}
export ROS_DOMAIN_ID=20
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 run camera_ros camera_node --ros-args \
  -p camera:=0 -p role:=video -p format:=BGR888 -p width:=1280 -p height:=720
```

This manual command bypasses the profile and is for isolated driver acceptance.
Stop the camera service first if it already owns the sensor. In another shell
with the same ROS/domain environment, check actual image delivery and CameraInfo:

```bash
ros2 topic hz /camera/image_raw
ros2 topic echo /camera/camera_info --once
```

Use the driver configuration selected in the hardware profile for normal service
operation. Calibrate intrinsics for the deployed resolution/configuration and
record camera/sensor mount transforms before geometry-dependent perception.
Uncalibrated CameraInfo publication does not provide usable camera geometry.

## Deploy the camera services on the commissioned Pi

From the Pi checkout, inspect the tracked profile before installation:

```bash
PYTHONPATH=deploy/pi python3 -m rover_hardware --profile config/hardware/ugv02-pi5.json check
PYTHONPATH=deploy/pi python3 -m rover_hardware --profile config/hardware/ugv02-pi5.json command camera
cd deploy/pi
bash ./install-visualization.sh
```

The installer requires working ROS, the camera overlay and non-interactive sudo.
It installs the hardware package under `/opt/rover`, the initial active profile
at `/etc/rover/hardware.json`, camera/video/bridge launchers and systemd units.
It starts/restarts the visualization services. The optional LiDAR unit is
installed but not enabled or started. Base control is not installed by it.

On later installs, the existing active profile is preserved and validated.
Pulling Git alone does not apply profile revisions to the running Pi. To apply
a tracked profile deliberately, run from the repository root:

```bash
PYTHONPATH=deploy/pi python3 -m rover_hardware --profile config/hardware/ugv02-pi5.json check
sudo install -m 0644 config/hardware/ugv02-pi5.json /etc/rover/hardware.json
sudo systemctl restart rover-camera.service
```

Review device paths and local parameters before that copy. For another active
profile or overlay, configure a systemd drop-in with `ROVER_HARDWARE_PROFILE`,
`ROVER_CAMERA_SETUP` or `ROVER_LIDAR_SETUP` as appropriate. Run `daemon-reload`
and restart affected units after unit/drop-in changes.

## Verify services, video and recovery

```bash
systemctl --no-pager status rover-camera.service rover-video.service rover-foxglove.service
journalctl -u rover-camera -u rover-video -u rover-foxglove -n 100 --no-pager
PYTHONPATH=/opt/rover python3 -m rover_hardware describe
```

Receive actual frames using the [PC viewer procedure](../../tools/pc/README.md).
Topic advertisement or an active service alone does not prove frame delivery.
The normal viewer uses the SSH-forwarded H.264 stream, not ROS JPEG/DDS transport.
Only one PC receiver can consume the current video stream at a time.

Measure visible end-to-end latency, verify disconnect/reconnect, and reboot the
Pi to confirm boot recovery and frame delivery. Record new results in a dated
archive record and update the feature checklist. The existing throughput results
are historical evidence; reboot and visible GUI acceptance remain outstanding.

## Commission the ESP32 base

The base driver and command gate are not implemented yet. The following steps
are their bring-up/acceptance procedure, not commands that enable existing ROS
motion services.

1. Identify the board, firmware, encoder connections and sensor orientation.
   Consult [base telemetry](UGV02_BASE_TELEMETRY.md) for vendor commands and
   raw-unit/orientation constraints. Use ROS Driver versus General Driver source
   appropriate to the delivered board; do not flash merely to match a document.
2. Verify power, UART pins/electrical levels and Linux device mapping before
   connecting. Check kernel console/getty ownership of that device; the archived
   Pi record found a serial console requiring deliberate resolution.
3. Query feedback without motion using the verified port/protocol. Record packet
   fields, units, resets, update timing and freshness during motor activity.
4. Implement the sole serial adapter and command gate with motion initially
   inhibited. Verify parsing, health, ownership, leases, limits and stop output.
   The nominal firmware timeout is backup protection, not the Pi's freshness gate.
5. Raise the wheels before enabling any motor command. Exercise low-speed
   directions, encoder scale and stops under expiry, disconnect and process exit.
6. Validate mobile power under combined camera/CPU/motor load, independent stop
   behavior and reboot/reset recovery before low-speed floor tests.
7. Establish one encoder/IMU odometry estimator and frame authority. Calibrate
   effective turning geometry and quantify slip; wheel speed is not exact ground
   velocity. Verify gyro conversion and sensor axes before fusion.

Keep manual and autonomy ownership explicit. Remote command freshness and PC/link
loss must be tested independently of successful status/video reception. ROS
names and types alone do not establish a safe motion path.

## Commission LiDAR and local navigation inputs

Follow the [LiDAR commissioning/swap procedure](HARDWARE_STACK.md#commission-the-ld06-or-swap-a-lidar)
for driver selection, serial paths, profile parameters and the optional service.
Verify real `/scan` data, units, timestamps, scan timing and the measured
`base_link -> lidar_link` transform. Record the actual driver's behavior.

Use the architecture's [frame ownership](../architecture/ROS_ARCHITECTURE.md#maps-localization-and-sensor-frames)
with verified odometry/IMU and scans. Build/save a repeatable geometric map,
check relocalization and coordinate corrections, and test navigation to ordinary
poses before using model-generated semantic destinations. Measure Pi load with
video active. Detailed package choice/configuration remains acceptance work.

The project's build milestones are maintained only in
[Feature status](../project/FEATURE_STATUS.md#suggested-next-sequence). This guide
supplies procedures for those milestones; it does not maintain another roadmap.
