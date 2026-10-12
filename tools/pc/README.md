# PC camera visualization and local analysis

This guide owns operation of the current Windows video/perception prototype.
The Pi runs ROS 2, camera_ros, an H.264 encoder and an optional diagnostic bridge.
The PC runs YOLO detection, Ollama scene descriptions and Foxglove presentation.
The normal video path uses SSH and does not require the ESP32 or a PC ROS install.
See [Feature status](../../docs/project/FEATURE_STATUS.md) for acceptance work.

The proposed next stage is [timestamped perception and semantic object memory](../../docs/architecture/PERCEPTION_AND_SEMANTIC_MAP.md): independent detection and model workers, saved object crops/full frames, measured location where available, asynchronous richer PC annotations, and shared map queries. This is a design, not an implemented feature; the current video pipeline still uses PC packet-arrival timestamps and has no semantic map write/read connection.

From the repository root:

```powershell
./tools/pc/start-viewer.ps1
```

In Foxglove, sign in if requested, then use **Layouts > Import from file** and choose
`tools/pc/foxglove-layout.json`. The launcher opens the local PC endpoint at
`ws://127.0.0.1:8766`. If the app does not connect automatically, choose
**Open connection > Foxglove WebSocket** and enter that URL.

The layout provides live video, a sampled frame with YOLO detector boxes and
a Qwen scene description, and the structured JSON result. If an Image panel does not select its topic after
import, select `/pc/camera/live` or `/pc/camera/analyzed` in its panel settings.
The layout import and visible panel rendering still need confirmation in the GUI.

The live path now uses H.264 video, not a sequence of JPEGs. The Pi encodes
1280x720 at 20 fps with FFmpeg/libx264, targeting 2 Mbps. It disables B-frames,
uses zero-latency encoding, and repeats SPS/PPS with a keyframe every second.
The encoder listens only on Pi localhost port 8554. The launcher forwards that
port over authenticated SSH; no new camera port is exposed on the LAN.
The PC demuxes MPEG-TS, forwards H.264 packets to Foxglove as
`foxglove.CompressedVideo`, and decodes frames with PyAV for local sampling.
JPEGs are created only for sampled model inputs and annotated snapshot output.
The [archived transport measurements](../../docs/archive/COMMISSIONING_2026-10-11.md#video-transport-revision-2026-10-11)
record throughput; visible camera-to-screen latency still needs measurement.
Live timestamps represent PC packet reception, not calibrated camera capture time.

The video stream supports one PC receiver. Stop the background pipeline before
running a foreground/one-frame check. On connection loss the Pi encoder service
restarts and the PC receiver retries. If the SSH tunnel exits, rerun the launcher.
The camera ROS publisher remains available locally for future robotics nodes;
the old compressed-image topic is no longer used by the PC pipeline.

The current model is the already installed Ollama `qwen2.5vl:7b`. Analysis uses only
the local API at `127.0.0.1:11434`. It samples the newest available frame after each
inference; it does not queue old images. The analyzed view shows the exact frame used
for inference, rather than applying delayed predictions to current video. Boxes are
produced by the local YOLO11s detector, with labels and confidence scores from that
same detection. Qwen supplies a scene summary, references to supplied detection
IDs and uncertainties. Detector coordinates are
in original-image pixels; the renderer never interprets Qwen coordinates or pairs
Qwen labels with detector boxes. The summary sits above the image rather than
obscuring its top edge. There is no connection from model output to motor control.

Qwen now receives **the clean resized camera frame plus matching structured JSON**.
The input includes an observation ID, the task, source/attached image sizes, up to
eight detector observations (IDs, labels, detector confidence and boxes scaled to
the attached image), and available robot context. The original full-size pixel
boxes are retained for comparison. IDs are local to one observation; persistent
tracking is not implemented. Qwen's response can reference only supplied IDs and
contains a summary and uncertainties; unexpected fields and invented IDs are rejected.
Detections remain hypotheses that Qwen can disagree with.

The default task is to observe and describe the scene. `--task` supplies another
observation question, for example `--task "Identify the chairs in this image"`.
This does not enable motion. Pose, map, navigation, LiDAR and object ranges are
unknown until real producers are connected; the prompt explicitly distinguishes
unknown measurements from visual impressions. The existing PC-receive timestamp
is labelled as such, and actual capture age stays unknown.

`runtime/qwen-input.json` records the structured input and `runtime/qwen-frame.jpg`
is the exact unannotated JPEG attached to the latest request. Foxglove also receives
the input on `/pc/vision/observation`; `/pc/vision/result` includes the frame ID and
validated model references. The separate `runtime/analyzed.jpg` is generated only
after inference for the viewer, and is never sent back into Qwen.

Future producers can optionally write a JSON snapshot selected with
`--robot-context-file PATH`. Its contract is an object with `updated_at_unix_s`
(Unix seconds) and optional `pose`, `map`, `navigation`, `lidar` objects or null.
Snapshots more than five seconds old, future-dated, malformed or missing become
unavailable context. This is a low-rate model context adapter, not camera/LiDAR
geometric fusion; sensor timestamp synchronization and calibration still need
implementation. The adapter cannot enable motion execution.

Seven automated checks cover clean-image input, landscape/portrait box scaling,
observation references, empty detections, unavailable geometry and context expiry:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tools/pc -p 'test_*.py' -v
```

A local Ollama integration check passed with the official sample image and five
matching detections: Qwen returned valid object references and explicitly noted
unknown positions and navigation state. The concise response took 3.23 seconds
on the warm model. Test evidence is in `runtime/qwen-test-*`; it is separate from
live request logs. The Pi remained unreachable, so live verification is pending.

YOLO11s detects the 80 common COCO categories; it will not box every arbitrary
object Qwen can describe. Detections below 50% confidence are omitted. Use
`--confidence` to change this threshold. Empty detections leave the frame unboxed.
It runs on the PC CPU to keep Ollama's GPU allocation independent. The detector
uses a 960-pixel inference size, restores boxes to original-image coordinates,
and records `coordinate_space`, `image_size`, `detector` and `detection_seconds`
in `runtime/analysis.json`. Labels remain predictions and need evaluation on
representative rover imagery, especially with low light, blur or unusual viewpoints.

The [archived detector/initial inference evidence](../../docs/archive/COMMISSIONING_2026-10-11.md)
records sample-image checks, the earlier real-frame model trial and their limits.
The current combined pipeline still needs live rover validation. This is sampled
scene analysis, not frame-rate detection; improve lighting and benchmark on
representative frames before relying on its descriptions or labels.

Inspect `runtime/vision.stderr.log` for current results and failures. The latest
source image, annotated image and JSON result are saved under `runtime/`, ignored
by Git. The background process does not start automatically with Windows.

To stop it, check the command line for the saved PID before stopping the process:

```powershell
$visionProcessId = [int](Get-Content runtime/vision.pid)
Get-CimInstance Win32_Process -Filter "ProcessId=$visionProcessId" | Select-Object ProcessId,CommandLine
# Once confirmed as tools/pc/camera_analysis.py:
Stop-Process -Id $visionProcessId
```

Use `./tools/pc/start-viewer.ps1 -VideoOnly` to start without model analysis when
the process is stopped. A running process retains its original mode.
For a foreground run, custom model, or one-frame validation:

```powershell
./.venv/Scripts/python.exe tools/pc/camera_analysis.py --once
./.venv/Scripts/python.exe tools/pc/camera_analysis.py --model qwen2.5vl:7b
```

For a fresh PC setup, install Python 3.12, Ollama and Foxglove desktop from their
official sites, install/pull a local vision model, then:

```powershell
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r tools/pc/requirements.txt
New-Item -ItemType Directory -Force runtime/models
curl.exe -L --fail https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt -o runtime/models/yolo11s.pt
```

For a CPU-only detection runtime, install `torch torchvision` from the official
`https://download.pytorch.org/whl/cpu` index before installing the requirements.
The default detector path is `runtime/models/yolo11s.pt`; `--detector` overrides it.
Weights are ignored by Git and must be downloaded for a fresh installation.

The commissioning PC has Foxglove 3.3.0 installed at `runtime/foxglove/Foxglove.exe`.
Adapt the launcher path if installed elsewhere. The PC Foxglove endpoint uses
subprotocol `foxglove.sdk.v1`. `--video-url` overrides the default
`tcp://127.0.0.1:8554` MPEG-TS input; the launcher supplies the SSH tunnel.
No ROS installation or DDS configuration is required on the PC for visualization.

For legacy JPEG diagnostics only, connect Foxglove to `ws://192.168.20.20:8765` and select
`/camera/image_raw/compressed` in an Image panel. This bypasses PC model analysis.
Keep the unencrypted Pi bridge on the trusted LAN.

References: [Foxglove connections](https://docs.foxglove.dev/docs/getting-started/frameworks/ros2),
[layout import](https://docs.foxglove.dev/docs/visualization/layouts),
[desktop launch](https://docs.foxglove.dev/docs/visualization/open-via-cli),
[local Ollama chat API](https://docs.ollama.com/api/chat).
[YOLO11 detector and supported classes](https://docs.ultralytics.com/models/yolo11).
