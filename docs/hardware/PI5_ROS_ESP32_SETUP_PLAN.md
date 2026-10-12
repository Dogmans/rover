# Pi 5 ROS 2 + ESP32 commissioning plan

This is the practical setup plan for configuring a Raspberry Pi 5 to work with the Waveshare UGV02 via its ESP32 controller and ROS 2.

See [Feature status](../project/FEATURE_STATUS.md) for the current cross-project checklist of implemented capabilities, outstanding validation, and planned work. This document retains commissioning procedures and recorded results.

## Recommended target stack

Visualization runs on the development PC. The Pi runs the camera publisher, ROS 2
runtime, Foxglove WebSocket bridge and, once the ESP32 arrives, the serial driver
and command safety gate. Foxglove desktop and local vision inference belong on
the PC; the Waveshare full Pi application and a Pi desktop are not required.

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

### Local SSH connection config

The repository-root `pi.sshconfig.local` file is machine-specific and ignored by Git. Copy `pi.sshconfig.example` to that path and set the Pi address and username for your setup. Keep passwords and private keys out of the repository; this config is set to use public-key authentication only. The local config can be used from PowerShell or a shell with:

```powershell
ssh -F .\pi.sshconfig.local rover-pi
```

Scripts can use the same OpenSSH config with `ssh -F <config-path> rover-pi` rather than duplicating connection details. If this file is absent, create it from the example; do not commit the local copy.

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

### Observed commissioning result (2026-10-11)

On `ROBOT`, Ubuntu Server 24.04.5 ARM64 with kernel `6.8.0-1064-raspi`, the kernel media graph detects the `imx708_wide` sensor. Ubuntu's packaged libcamera 0.2 lacked the PiSP pipeline handler, so its `cam -l` did not enumerate the sensor. The direct V4L2 stream test on `/dev/video0` is not a valid end-to-end camera acceptance test for the Pi 5 CSI pipeline.

Installed the Raspberry Pi libcamera fork `v0.7.2+rpt20261009` and `rpicam-apps` `1.13.0` under `/usr/local`, with the PiSP pipeline and IPA enabled. Ubuntu Noble's FFmpeg libraries are too old for the current rpicam libav encoder, so this build has libav disabled; still capture and MJPEG video work. Verified a 4608x2592 JPEG and a short 640x480 MJPEG recording. No OS reimage was needed.

Installed ROS 2 Jazzy base, rosdep/colcon, and Foxglove bridge `3.6.0`. The packaged `camera_ros` executable was ABI-incompatible with the Raspberry Pi libcamera build, so `camera_ros` `0.7.0` was built in `/home/barry/camera_ws` against the working PiSP library, with a local compatibility adjustment for `std::dynamic_extent`. The node was verified publishing `/camera/image_raw` (`rgb8`) and `/camera/camera_info` at approximately 30 Hz using 1280x720 BGR888 output.

The camera is not calibrated yet. `CameraInfo` publishes, but its intrinsic dimensions are zero until a calibration file is created; do not use it for geometry-dependent perception before calibration. No object-detection or model-labelling node is installed.

The Foxglove bridge was verified reachable from the development PC on `ws://192.168.20.20:8765` and advertised the camera topics. It binds to all interfaces without TLS, so keep it on the trusted LAN. The temporary camera and bridge processes were stopped after validation.

To start the camera publisher in a shell:

```bash
source /opt/ros/jazzy/setup.bash
source ~/camera_ws/install/setup.bash
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH
ros2 run camera_ros camera_node --ros-args -p camera:=0 -p role:=video -p format:=BGR888 -p width:=1280 -p height:=720
```

In a second shell, start the Foxglove bridge:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765 address:=0.0.0.0
```

### Persistent video and PC analysis setup (2026-10-11)

Installed `ros-jazzy-compressed-image-transport` 4.0.7 and deployed the versioned
service definitions and launch scripts in `deploy/pi/`. Both `rover-camera` and
`rover-foxglove` are enabled at boot and currently running as user `barry`, using
`ROS_DOMAIN_ID=20` and `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`. Boot enablement
is verified; a full reboot acceptance test remains outstanding. These paths are
specific to this commissioned Pi and its `/home/barry/camera_ws` overlay.

Camera output is 1280x720. The bridge serves raw images, compressed JPEG images,
CameraInfo and diagnostics. The PC received a compressed camera message of
332173 bytes via `ws://192.168.20.20:8765`. The first service start advertised
topics but did not deliver frames; restarting both services restored delivery.
If this recurs, inspect the journals and verify frame delivery, not just topic names.

```bash
sudo systemctl status rover-camera rover-foxglove
journalctl -u rover-camera -u rover-foxglove -n 100 --no-pager
sudo systemctl restart rover-camera rover-foxglove
```

Manual ROS inspection commands must use the same domain/discovery environment.
Use `--no-daemon` where supported to avoid an old ROS CLI daemon's configuration.
Direct PC Foxglove viewing uses the bridge WebSocket, so PC ROS/DDS installation
is unnecessary. Future PC ROS command/perception nodes need a separately tested
network configuration; the current local-only DDS scope is for camera visualization.

Installed official Foxglove desktop 3.3.0 on the PC under `runtime/foxglove/`.
Added the PC receiver, local Ollama inference, and annotated-frame publisher under
`tools/pc/`. It uses the already installed `qwen2.5vl:7b` model, runs inference on
the PC, and exposes `ws://127.0.0.1:8766` with live and analyzed-image topics.
One real image was analyzed successfully in 84.6 seconds on the first call;
subsequent warm calls took approximately 2.4–3.0 seconds at a five-second sampling
interval. This is a scene-analysis experiment, not a frame-rate detector; model
labels varied on the dim/noisy feed and box accuracy is unvalidated. The analyzed
view retains the exact source frame to avoid applying stale overlays to live video.
See [PC viewer instructions](../../tools/pc/README.md) for the launcher and layout
import. GUI sign-in, layout import and visible rendering require user confirmation.

The ESP32 has not arrived. UART and motor commissioning are deferred. Read-only
inspection found an active `serial-getty@ttyAMA0` and `console=serial0,115200` in
the boot command line. `/dev/serial0` is not currently a resolved device symlink.
Confirm actual header pins and board revision before freeing/configuring a UART;
no serial probes or movement commands were sent.

### Video transport revision (2026-10-11)

The PC viewer now uses an encoded H.264 stream instead of receiving ROS JPEG
frames. The earlier JPEG path measured only 4.1 fps at 9.08 Mbps at the PC endpoint.
The replacement measured 20.07 fps at 2.02 Mbps with the live channel advertised
as `foxglove.CompressedVideo`. This is a throughput measurement; end-to-end visible
latency still needs a physical camera-to-screen test.

Added and enabled `rover-video.service`: it subscribes to local raw ROS camera
images and encodes 1280x720 H.264 with FFmpeg/libx264 at 20 fps, targeting 2 Mbps.
It uses zero-latency settings, no B-frames, repeated SPS/PPS, a one-second keyframe
interval and zero MPEG-TS mux delay. Pi 5 uses software encoding in this setup.
The encoder listens only at `127.0.0.1:8554`; the PC launcher opens an authenticated
SSH tunnel using `pi.sshconfig.local`. No new LAN listener was added.

The PC receiver demuxes the MPEG-TS stream, forwards H.264 access units to Foxglove
and decodes frames locally with PyAV. Only sampled analysis frames and rendered
overlay snapshots are converted to JPEG on the PC. Live packet timestamps are PC
receive times, not calibrated capture timestamps. The existing `/pc/camera/live`
topic and Foxglove layout remain in use. The ROS compressed-image topic is retained
for diagnostics but is no longer part of the PC viewing/analysis path.

The encoder supports one receiver at a time. Stop the background PC receiver before
using `--once`; rerun the launcher if its SSH tunnel exits. The Pi encoder restarts
after a client disconnect and the PC receiver retries. Check runtime logs for decoded
fps and bitrate. Automatic boot recovery still requires the outstanding reboot test.

Reference: [Foxglove encoded-video requirements](https://docs.foxglove.dev/docs/sdk/schemas/compressed-video).

## 5. Install ROS 2

### Structured Qwen observations (2026-10-11)

Qwen receives an unannotated sampled frame and structured evidence from that same
frame. The PC input includes the observation task, frame ID, explicit PC-reception
timestamp basis, dimensions, detector IDs/labels/confidence, and boxes scaled to the
attached model image. Missing pose/map/navigation/LiDAR/range data stays unknown.
Object IDs are observation-scoped; persistent tracking and sensor association are
not implemented. The model responds with a description, supplied object references
and uncertainties. The response schema and local validator reject invented IDs
and additional fields; model output has no motion-execution path.

The input is inspectable as `/pc/vision/observation` and in `runtime/qwen-input.json`,
with the actual clean attached JPEG at `runtime/qwen-frame.jpg`. Optional future
robot-context file snapshots expire after five seconds. Seven automated checks
cover alignment, clean input, missing geometry, references and stale context.
The Pi was unreachable during the change, so a live-stream check remains pending.
An actual local Qwen request with a clear sample image and five detections returned
validated IDs and unknown-geometry statements in 3.23 seconds on the warm model.

### Object-box revision (2026-10-11)

Replaced Qwen-generated coordinates with PC-side YOLO11s detections. Qwen was
returning coordinates above 1000 despite the requested 0-1000 convention, making
the earlier overlay unreliable. Qwen now produces only a scene summary; detector
boxes, labels and confidence come from the same prediction in original-image
pixels. The summary banner is placed outside the image so it cannot cover boxes.

The detector runs on the PC CPU at 960-pixel inference size with a 0.5 confidence
threshold, using the 80 COCO categories. It does not cover arbitrary descriptions
or guarantee correctness in dim/blurred scenes. A clear official sample showed
aligned bus/person boxes; the saved dim rover frame produced no confident boxes.
The Pi was unreachable during this update, so live validation remains outstanding.
See `tools/pc/README.md` for model download, settings and limitations.

Use Ubuntu Server 24.04 ARM64 + ROS 2 Jazzy as the selected baseline. Install the official Jazzy deb packages for Ubuntu 24.04 ARM64 and record the image date, kernel, ROS package versions and install steps in the hardware log. Do not use the Waveshare full Pi image or run its `ugv_rpi` installer as a prerequisite.

On this Pi the CSI camera acceptance gate is passed, including local still/video capture and ROS image/CameraInfo publication. For a fresh installation, keep this as a go/no-go gate before installing the full ROS workspace; if it fails, investigate the matching PiSP-capable libcamera stack before considering an OS change.

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
   - fuses verified wheel encoder and onboard IMU data; the controller board
     includes an ICM-20948, with telemetry conversion/quality to commission

See [UGV02 onboard IMU and encoder telemetry](UGV02_BASE_TELEMETRY.md) for the
documented JSON interface and upstream firmware details. Do not assume raw
IMU values already have ROS units or that returned orientation is valid.

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

Current execution state and next steps:

1. Ubuntu, ROS base, CSI capture and ROS camera publication are complete.
2. Camera and Foxglove bridge services are deployed and enabled; verify automatic
   recovery after a Pi reboot and repeat the PC compressed-frame check.
3. Open the PC Foxglove client and import `tools/pc/foxglove-layout.json`; confirm
   live video and the sampled-frame overlays in the GUI.
4. Improve camera lighting, calibrate at the deployed resolution, then benchmark
   local vision latency and accuracy. A smaller VLM or dedicated detector may be
   needed for frequent overlays.
5. Await the ESP32, then verify board revision, firmware, power and UART wiring.
6. Resolve the serial console/device mapping, query status without motion, then
   implement the serial driver and freshness gate against the confirmed protocol.
7. Validate wheels-up motion, watchdog stops, crashes and network loss before floor tests.

For a fresh Pi installation, the working sequence is:

1. Image the SD card with Ubuntu Server 24.04 LTS 64-bit ARM.
2. Boot and configure the Pi.
3. Enable SSH and network.
4. Install camera stack and verify the camera.
5. Install ROS 2.
6. Consult the matching Waveshare firmware source as a protocol reference; the host installer is optional and not part of this baseline.
7. Verify the ESP32 board revision and firmware.
8. Connect the Pi UART to the ESP32 and confirm the serial protocol.
9. Run a simple low-speed JSON command with the wheels lifted.
10. Build a minimal ROS 2 bridge for drive commands and status.
11. Validate command freshness, stop behavior and watchdog recovery.
12. Move to camera-first experiments and then autonomy development.

This plan is designed to be the first reproducible setup path, not the final unchanging architecture. It must be tested on the real hardware and updated as soon as board revision, power draw, and protocol details are confirmed.
