# Pi 5 ROS 2 + ESP32 commissioning plan

This is the practical setup plan for configuring a Raspberry Pi 5 to work with the Waveshare UGV02 via its ESP32 controller and ROS 2.

## Recommended target stack

Use the following as the default build path unless the exact hardware and board revision force a different variant:

- Raspberry Pi OS 64-bit (Bookworm) on the Pi 5
- ROS 2 Jazzy on Ubuntu 24.04 ARM64 or a compatible ROS 2 package source if Debian packaged binaries are available
- Official Raspberry Pi camera stack (`libcamera`, `rpicam-apps`, Picamera2 when needed)
- Waveshare UGV02 ESP32 firmware as the low-level chassis controller
- ROS nodes that translate between ROS 2 topics and the JSON UART command protocol used by the ESP32

This recommendation reflects the official Raspberry Pi camera guidance and the Waveshare robot docs. The vendor example repo also targets Raspberry Pi OS and host-side scripts, so the practical path is to validate the actual board revision, UART wiring and protocol before deciding whether to stay on Raspberry Pi OS or switch to Ubuntu 24.04.

## 1. Hardware verification before software install

Before you begin flashing or installing ROS, confirm the hardware and board revision:

1. Confirm the exact chassis and shipped driver board revision.
   - Check whether it is the newer ROS Driver for Robots board or the older General Driver board.
   - Do not assume the board revision from a generic listing.
2. Verify the power and battery configuration.
   - Three 18650 cells in series are expected.
   - Check the battery condition, polarity, and the UPS module status.
   - Confirm the Pi 5 power budget under load and test with the camera and motors active.
3. Verify the connection plan to the ESP32.
   - The UGV02 docs specify a host computer interface via GPIO UART at 115200 baud.
   - Confirm the exact UART pins and wiring, and test on the bench before mounting the Pi in the robot.
4. Verify the camera path.
   - The camera is a Raspberry Pi Camera Module 3 Wide, which uses the official CSI stack.
   - Confirm the camera cable is the correct 22-pin Pi-side to 15-pin camera-side cable.

## 2. Prepare the SD card and Pi OS

Use Raspberry Pi Imager and configure the OS before the first boot.

### 2.1 Install Raspberry Pi Imager

Download and install from:

- https://www.raspberrypi.com/software/

### 2.2 Flash Raspberry Pi OS 64-bit

Use Raspberry Pi Imager with:

- Device: Raspberry Pi 5
- OS: Raspberry Pi OS (64-bit)
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

## 3. Configure the Raspberry Pi system

After the Pi is reachable over the network:

```bash
sudo raspi-config
```

Recommended first-pass changes:

- System Options > Hostname
- Localisation > Timezone / locale
- Interface Options > SSH enable
- Performance Options > set memory split if applicable to camera/graphics use
- Interface Options > enable I2C if required by future peripherals
- Interface Options > serial console disable only if you are using the serial UART for the ESP32

Important: if the Pi's serial port is being used for the ESP32, do not leave the system console tied to it. Confirm the actual UART mapping before relying on it.

## 4. Install the camera software stack

The camera is a Raspberry Pi CSI camera. Use the modern Raspberry Pi camera stack rather than the legacy stack.

Verify the camera is visible:

```bash
v4l2-ctl --list-devices
libcamera-hello --list-cameras
```

If the package is not present, install the camera stack:

```bash
sudo apt install -y libcamera-apps python3-picamera2
```

Then test the camera with:

```bash
libcamera-hello -t 2000
rpicam-still -o test.jpg
```

This matches the official Raspberry Pi camera documentation, which states that the modern camera stack is the supported route and that legacy `raspistill`/`raspivid` paths are deprecated.

## 5. Install ROS 2

### Option A: recommended practical path

For a clean, current workstation-class ROS install on the Pi:

- Ubuntu 24.04 ARM64 on the Pi 5
- ROS 2 Jazzy

This is the cleanest long-term approach if the project wants to stay fully in ROS 2 with standard tooling.

### Option B: vendor-compatible path

If the project wants the shortest path to the vendor sample repo and script flow, use:

- Raspberry Pi OS 64-bit
- ROS 2 packages via the appropriate Debian repository or Dockerized ROS install
- then follow the Waveshare `ugv_rpi` and `ugv_base_ros` examples

For the initial project plan, we treat Ubuntu 24.04 + ROS 2 Jazzy as the preferred target and Raspberry Pi OS as the compatibility fallback.

### ROS install pattern

For Ubuntu 24.04 ARM64, the standard ROS 2 Jazzy flow is:

```bash
sudo apt update
sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

 echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update
sudo apt install -y ros-jazzy-desktop
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

## 7. Install the ESP32 low-level firmware and verify the protocol

The lower computer repo is:

- https://github.com/waveshareteam/ugv_base_ros

This is the ESP32 firmware to inspect and compile if needed. The official docs also state that the ESP32 uses JSON commands over UART at 115200 baud.

### 7.1 Verify board revision and firmware

Before compiling or changing firmware, inspect the board and determine whether it is the newer ROS Driver board or the older General Driver board.

The repository naming suggests:

- `ugv_base_ros` for ROS Driver boards
- `ugv_base_general` for older General Driver boards

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

The UGV02 docs list JSON control patterns including command types such as:

- wheel speed control
- motor PWM debug mode
- ROS control mode
- chassis feedback queries
- continuous serial feedback

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

Replace `/dev/ttyUSB0` with the actual UART path after checking the hardware.

## 10. Camera-first validation

Before adding a large autonomy stack:

1. Verify `libcamera` sees the camera.
2. Capture stills and video locally.
3. Publish a camera stream into ROS 2.
4. Validate latency and image quality.
5. Use the feed for simple motion or target detection experiments.

Recommended camera test commands:

```bash
libcamera-hello -t 2000
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

1. Image the SD card with Raspberry Pi OS 64-bit.
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
