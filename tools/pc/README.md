# PC camera visualization and local analysis

The Pi runs ROS 2, camera_ros, an H.264 encoder, and foxglove_bridge. Foxglove desktop, the vision model,
and overlay rendering run on the Windows PC. No ESP32 is needed for this path.

From the repository root:

```powershell
./tools/pc/start-viewer.ps1
```

In Foxglove, sign in if requested, then use **Layouts > Import from file** and choose
`tools/pc/foxglove-layout.json`. The launcher opens the local PC endpoint at
`ws://127.0.0.1:8766`. If the app does not connect automatically, choose
**Open connection > Foxglove WebSocket** and enter that URL.

The layout provides live video, the sampled frame with model-generated boxes and
description, and the JSON result. If an Image panel does not select its topic after
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
Measured after migration: 20.1 decoded fps at approximately 2.03 Mbps,
versus the previous JPEG viewer measurement of 4.1 fps and 9.08 Mbps.
This verifies throughput, not complete camera-to-screen latency.
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
experimental model predictions, not a validated object detector. Invalid coordinates
are omitted. There is no connection from model output to motor control.

The first real-frame test on 2026-10-11 took 84.6 seconds and produced a description
and object boxes. Subsequent warm calls took approximately 2.4–3.0 seconds, with
sampling every five seconds. This is a sampled scene-analysis overlay, not a
frame-rate detector. Labels varied on the dim, noisy test image. Improve scene lighting before evaluating
accuracy; a smaller vision model or dedicated detector is a subsequent benchmark.

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
```

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
