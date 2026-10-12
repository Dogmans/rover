# Commissioning record: 11 October 2026

Historical evidence from the Pi camera, ROS publication, video transport and PC
perception commissioning session. Statements about running processes, package
versions and outstanding work describe that session; they are not a fresh health
check or instructions for a new installation.

For current status, use [Feature status](../project/FEATURE_STATUS.md). For current
procedures, use the [Pi commissioning guide](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md)
and [PC viewer guide](../../tools/pc/README.md).

## Pi camera and services

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

## PC perception revisions

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
