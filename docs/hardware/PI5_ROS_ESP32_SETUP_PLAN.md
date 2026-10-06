# Pi 5 ROS 2 + ESP32 commissioning plan

This is the practical setup plan for configuring a Raspberry Pi 5 to work with the Waveshare UGV02 via its ESP32 controller and ROS 2.

## Recommended target stack

Use the following as the default build path. This is a selected baseline, not yet a validated image; the camera test below is an early go/no-go gate.

- Ubuntu Server 24.04 LTS, ARM64, on the Pi 5
- ROS 2 Jazzy binary packages for Ubuntu 24.04 ARM64
- Official Raspberry Pi camera stack (`libcamera`, `rpicam-apps`, Picamera2 when needed)
- Waveshare UGV02 ESP32 firmware as the low-level chassis controller
- A project-owned Pi ROS node that translates between ROS 2 and the ESP32 JSON UART protocol

Jazzy on Ubuntu is the cleanest supported ROS binary-package path for this Pi 5 project. Raspberry Pi documents IMX708 support in its camera stack, but do not assume that the exact CSI camera path works on the selected Ubuntu image: prove capture and ROS image publication before proceeding. If that gate fails, stop and choose a Raspberry Pi OS-based ROS deployment deliberately. Waveshare's `ugv_base_ros` is ESP32 firmware, not a ROS 2 host driver, and its full Pi application is not required.

## 1. Hardware verification before software install

Before you begin flashing or installing ROS, confirm the hardware and board revision:

1. Confirm the exact chassis and shipped driver board revision.
   - Check whether it is the newer ROS Driver for Robots board or the older General Driver board.
   - Do not assume the board revision from a generic listing.
2. Verify the power and battery configuration.
   - Three 18650 cells in series are expected.
   - Check the battery condition, polarity, and the UPS module status.
   - The vendor board advertises 5 V/3.3 V outputs without a verified continuous current rating for Pi 5 use. Power the Pi from a separate known 5 V/5 A supply during bench bring-up; do not connect board 5 V to Pi power until rated and wired safely.
   - Test the final battery-to-Pi regulator under CPU, camera and motor load for voltage dips, resets and undervoltage before mobile operation.
3. Verify the connection plan to the ESP32.
   - The UGV02 docs specify a host computer interface via GPIO UART at 115200 baud.
   - Confirm the exact UART pins and wiring, and test on the bench before mounting the Pi in the robot.
4. Verify the camera path.
   - The camera is a Raspberry Pi Camera Module 3 Wide, which uses the official CSI stack.
   - Confirm the camera cable is the correct 22-pin Pi-side to 15-pin camera-side cable.

## 2. Prepare the SD card and Ubuntu Server

Use Raspberry Pi Imager and configure the OS before the first boot.

### 2.1 Install Raspberry Pi Imager

Download and install from:

- https://www.raspberrypi.com/software/

### 2.2 Flash Ubuntu Server 24.04 LTS (64-bit ARM)

Use Raspberry Pi Imager with:

- Device: Raspberry Pi 5
- OS: Ubuntu Server 24.04 LTS (64-bit ARM)
- Storage: the microSD card

Enable these during imaging if using a headless setup:

- hostname
- Wi-Fi credentials
- username and password
- SSH access

This matches the official Raspberry Pi OS setup instructions.

### 2.3 First boot and networking

After the SD card is inserted and powered on:

1. Boot the Pi and confirm the OS starts.
2. Connect to the network via Ethernet or Wi-Fi.
3. Confirm the hostname and SSH access are working.
4. Run the first update sequence:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

## 3. Configure Ubuntu Server and the Pi interfaces

Preconfigure hostname, user, Wi-Fi and SSH with Raspberry Pi Imager. After first boot, update Ubuntu and verify the Pi is reachable over the intended LAN. Do not assume Raspberry Pi OS utilities are present.

```bash
sudo apt update
sudo apt full-upgrade -y
```

Before enabling the ESP32 UART, confirm the exact board pinout and Linux device mapping. Use the Ubuntu Raspberry Pi documentation to ensure the UART is enabled and that no kernel console owns that UART. Do not use `raspi-config`-specific menu steps or change GPU memory settings for this headless Ubuntu baseline.

The camera acceptance test and UART mapping should be completed before mounting the Pi in the chassis. Use a known 5 V/5 A USB-C supply for bench work; the chassis 5 V output is not approved as a Pi supply until its rating is known.

## 4. Install the camera software stack

The camera is a Raspberry Pi CSI camera. Use the modern libcamera-based stack, not the legacy stack. Ubuntu package/tool availability can differ from Raspberry Pi OS, so do not assume `rpicam-*` is preinstalled.

Verify the camera is visible:

```bash
v4l2-ctl --list-devices
cam -l
```

Install the Ubuntu camera utilities available for the selected image, then verify that the IMX708 sensor enumerates. On Raspberry Pi OS, the equivalent application is `rpicam-hello --list-cameras`; use `rpicam-still`/`rpicam-vid` only when those applications are installed and support the CSI camera.

```bash
sudo apt install -y v4l-utils libcamera-tools
```

Pass the camera gate by capturing a local still and short video, then publishing timestamped images and CameraInfo through the selected ROS 2 camera driver. If Ubuntu cannot provide that complete path, stop and reassess the OS before continuing.

This matches the official Raspberry Pi camera documentation, which states that the modern camera stack is the supported route and that legacy `raspistill`/`raspivid` paths are deprecated.

## 5. Install ROS 2

Use Ubuntu Server 24.04 ARM64 + ROS 2 Jazzy as the selected baseline. Install the official Jazzy deb packages for Ubuntu 24.04 ARM64 and record the image date, kernel, ROS package versions and install steps in the hardware log. Do not use the Waveshare full Pi image or run its `ugv_rpi` installer as a prerequisite.

Before installing the full ROS workspace, pass the CSI camera acceptance gate: confirm IMX708 enumeration, capture a local image/video, and publish a ROS image with timestamps and CameraInfo. If this fails on Ubuntu, pause and reassess a Raspberry Pi OS-based ROS setup before proceeding; the fallback is intentionally not preselected because camera, ROS packaging and host integration must be tested together.

### ROS install pattern

For Ubuntu 24.04 ARM64, the standard ROS 2 Jazzy flow is:

```bash
sudo apt update
sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

 echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update
sudo apt install -y ros-jazzy-ros-base
```

Then source the environment:

```bash
source /opt/ros/jazzy/setup.bash
```

Set it for every shell:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## 6. Install the Waveshare host-side example

Clone the Waveshare host repo:

```bash
git clone https://github.com/waveshareteam/ugv_rpi.git
cd ugv_rpi
sudo chmod +x setup.sh autorun.sh
sudo ./setup.sh
./autorun.sh
```

Important: do this only if using the Waveshare host-side scripting path. It is a practical vendor example, not a guarantee that it is the final architecture for a custom ROS 2 stack.

If the repo is not used directly, keep it as a reference for the working host-side deployment pattern and the expected robot configuration values.

## 7. Verify the ESP32 low-level firmware and protocol

The lower computer repo is:

- https://github.com/waveshareteam/ugv_base_ros

This repository is the ESP32 firmware source, not a ROS 2 host-side package. Keep the shipped firmware initially; do not compile or flash unless the delivered board/version requires it. UGV02 documentation identifies version 0.96 as current and documents JSON over UART at 115200 baud.

### 7.1 Verify board revision and firmware

Read the board markings and OLED firmware/version at boot. Determine whether it is the newer ROS Driver board or older General Driver board before choosing source or pin assignments. Current UGV02 documentation says older UGV02 units use General Driver; newer ROS Driver units use `ugv_base_ros`.

The repository roles are:

- `ugv_base_ros` for ROS Driver boards
- `ugv_base_general` for older General Driver boards

Despite its name, `ugv_base_ros` runs on the ESP32; the Pi still needs a ROS-to-serial bridge.

### 7.2 Confirm the host UART connection

On Raspberry Pi, use:

```bash
ls /dev/serial*
ls /dev/tty*
```

Check the port exposed for the ESP32 connection and test a serial loop or basic JSON probe.

For the Pi-side host, the relevant serial port may appear as `/dev/ttyAMA0`, `/dev/ttyS0`, or a USB serial adapter path depending on the chosen wiring and board revision. Verify with `dmesg` or `journalctl -k` if necessary.

## 8. Build the ROS bridge / interface layer

The ESP32 expects JSON commands. The Pi should not send motor commands raw without a defined protocol layer and safety checks.

Plan the following ROS nodes:

1. `esp32_serial_bridge`
   - handles UART framing and parsing
   - converts ROS messages to JSON
   - receives status JSON and republishes to ROS topics
2. `drive_controller`
   - takes `cmd_vel` or a custom command type
   - enforces freshness, scale limits, and stop logic
3. `robot_state_publisher` / URDF
   - publishes transforms for base_link, chassis, camera, etc.
4. `camera_node`
   - publishes camera feed and camera info using the Pi camera stack
5. `odom_node`
   - fuses wheel encoder and IMU data, if available

Do not implement multiple duplicate differential-drive or odometry stacks. Keep a single source-of-truth for velocity representation and one consistent odometry node.

## 9. Key serial and control commands to test

The current UGV02 reference documents newline-delimited JSON at 115200 baud. Prefer the ROS-style velocity command, not raw PWM:

- `{"T":13,"X":0.1,"Z":0.0}`: linear m/s and angular rad/s.
- `{"T":1,"L":0.1,"R":0.1}`: closed-loop left/right wheel speeds in m/s; documented range is -0.5 to +0.5.
- `{"T":130}`: request chassis feedback.
- `{"T":131,"cmd":1}`: enable continuous chassis feedback.

The firmware source sets a 3000 ms heartbeat stop. The Pi command gate must use a much shorter local freshness timeout and send zero/stop when its command lease expires; the MCU timeout is a backup only. Verify actual behavior with wheels elevated.

Operational test flow:

1. Boot ESP32 and check that UART is alive.
2. Query chassis or status feedback.
3. Send a low-speed command with the wheels lifted.
4. Confirm the command is accepted and feedback is read back.
5. Confirm the robot stops when the heartbeat or command timeout is exceeded.
6. Confirm the robot can be commanded and then safely stopped using a watchdog.

Example serial test pattern:

```bash
python3 - <<'PY'
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser.write(b'{"T":130}\n')
print(ser.readline())
PY
```

Replace `/dev/ttyUSB0` with the verified UART path. The Pi 40-pin header exposes UART/I2C only (not general-purpose GPIO); check the board schematic and voltage levels before wiring.

## 10. Camera-first validation

Before adding a large autonomy stack:

1. Verify `libcamera` sees the camera.
2. Capture stills and video locally.
3. Publish a camera stream into ROS 2.
4. Validate latency and image quality.
5. Use the feed for simple motion or target detection experiments.

Use the camera commands installed for the selected OS. Raspberry Pi OS uses `rpicam-*`; Ubuntu may provide `cam`/libcamera tools instead. These command names are examples, not a guarantee that both command sets are present:

```bash
cam -l
rpicam-still -o test.jpg
rpicam-vid -t 5000 -o test.h264
```

For ROS camera publishing, use a standard ROS 2 camera driver or image transport package that matches the chosen ROS distribution.

## 11. ROS network and command freshness requirements

The project should impose the following safety rules for the Pi and the PC:

- Use ROS 2 over local network only.
- Set `ROS_DOMAIN_ID` explicitly.
- Use timestamps on motion commands.
- Reject stale commands.
- Stop on network loss or process crash.
- Keep manual and autonomous control ownership explicit.
- Ensure the ESP32 watchdog/heartbeat is not bypassed by an old stale command.

This is important because the UGV02 docs explicitly mention a heartbeat-based safety stop if no movement command is received within a short period.

## 12. Commissioning sequence on the bench

Use this order before moving the robot onto the floor:

1. Test power on the bench without driving wheels.
2. Confirm the Pi powers correctly with the camera connected.
3. Confirm UART to the ESP32 is stable and the JSON protocol responds.
4. Confirm the Pi can read status and send motion commands.
5. Lift the robot so the wheels are not touching the ground.
6. Run low-speed movement commands with the chassis elevated.
7. Verify directionality, encoder feedback and speed scaling.
8. Test stop behavior under command timeout and disconnect conditions.
9. Test process crash behavior.
10. Test network loss behavior.
11. Only then move to floor tests and low-speed motion trials.

## 13. Minimum validation checklist before autonomy experiments

A successful Pi + ROS + ESP32 integration should satisfy all of the following:

- Pi boots reliably from the SD card
- Camera is recognized and visible via the Raspberry Pi camera stack
- UART is stable and JSON commands reach the ESP32
- Chassis feedback is readable
- Motor commands can be issued and verified
- Robot stops under timeout / stale command conditions
- ROS topics are published and consumed as expected
- Camera feed is available on the network
- A safe stop and watchdog path exists even if the Pi restarts

## 14. Unresolved decisions to keep explicit

Keep these assumptions visible until they are verified on actual hardware:

- exact board revision and firmware type
- UART pin mapping and pinout on the delivered board
- whether the board is newer ROS Driver or older General Driver
- Pi 5 power budget with camera and active cooler under load
- encoder availability and odometry semantics
- whether a custom ROS bridge is needed beyond a simple serial translator
- final OS distribution choice between Raspberry Pi OS and Ubuntu 24.04 + ROS 2 Jazzy

## 15. Next execution tasks

When the hardware is available, the working sequence is:

1. Image the SD card with Ubuntu Server 24.04 LTS 64-bit ARM.
2. Boot and configure the Pi.
3. Enable SSH and network.
4. Install camera stack and verify the camera.
5. Install ROS 2.
6. Clone the Waveshare host and lower-computer source repos.
7. Verify the ESP32 board revision and firmware.
8. Connect the Pi UART to the ESP32 and confirm the serial protocol.
9. Run a simple low-speed JSON command with the wheels lifted.
10. Build a minimal ROS 2 bridge for drive commands and status.
11. Validate command freshness, stop behavior and watchdog recovery.
12. Move to camera-first experiments and then autonomy development.

This plan is designed to be the first reproducible setup path, not the final unchanging architecture. It must be tested on the real hardware and updated as soon as board revision, power draw, and protocol details are confirmed.
