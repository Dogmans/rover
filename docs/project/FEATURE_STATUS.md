# Feature status

Last reviewed: 2026-10-12.

This is the authoritative checklist of implemented capabilities, acceptance work
and next project milestones. It summarizes repository code and recorded
commissioning results; it is not a fresh live-hardware test.

[Project notes](PROJECT_NOTES.md) explain goals and rationale. The
[ROS architecture](../architecture/ROS_ARCHITECTURE.md) owns the target design,
the [Pi guide](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md) owns procedures, and the
[dated archive](../archive/README.md) preserves bring-up evidence.

The working baseline is camera streaming and sampled local scene analysis. The
ESP32 has not arrived according to the latest commissioning record, so motor
control and autonomous operation remain unimplemented.

## Implemented

Implemented means code or a commissioned component exists. Validation limits are
listed separately below; these entries do not imply readiness for autonomous use.

| Feature | Current capability | Evidence / implementation |
| --- | --- | --- |
| Pi OS and ROS runtime | Ubuntu Server 24.04 ARM64 and ROS 2 Jazzy installed on the commissioned Pi. | [Commissioning results](../archive/COMMISSIONING_2026-10-11.md#observed-commissioning-result-2026-10-11) |
| Hardware profile and replaceable sensor adapters | Versioned hardware selection, shared ROS topic contracts and profile-driven camera launcher; generic ROS LaserScan adapter and optional disabled LiDAR service. Repository implementation; updated deployment not yet verified on the Pi. | [Hardware stack](../hardware/HARDWARE_STACK.md), [Pi adapters](../../deploy/pi/rover_hardware/), [hardware profile](../../config/hardware/ugv02-pi5.json) |
| CSI camera capture and ROS publication | Camera Module 3 Wide still/video capture verified; raw images and uncalibrated CameraInfo published at approximately 30 Hz. | [Camera commissioning](../archive/COMMISSIONING_2026-10-11.md#observed-commissioning-result-2026-10-11), [camera launcher](../../deploy/pi/rover-camera.sh) |
| Persistent Pi camera and bridge services | Versioned systemd units and installer; camera, Foxglove bridge and video encoder enabled at boot. | [Deployment installer](../../deploy/pi/install-visualization.sh), [service commissioning](../archive/COMMISSIONING_2026-10-11.md#persistent-video-and-pc-analysis-setup-2026-10-11) |
| Pi ROS observability bridge | Foxglove WebSocket bridge exposes camera topics and diagnostics on the trusted LAN. | [Bridge launcher](../../deploy/pi/rover-foxglove.sh), [bridge check](../../deploy/pi/check-foxglove.ps1) |
| H.264 video transport to PC | 1280x720 at 20 fps over an SSH tunnel; measured approximately 20 decoded fps at 2 Mbps. Single PC receiver; receiver retry and encoder restart behavior implemented. | [Pi encoder](../../deploy/pi/rover-video.py), [PC receiver](../../tools/pc/camera_analysis.py), [transport evidence](../archive/COMMISSIONING_2026-10-11.md#video-transport-revision-2026-10-11) |
| PC viewer launcher and layout | Launcher starts the tunnel and local pipeline, opens Foxglove, and supports video-only mode; importable layout provides live video, sampled analysis and JSON panels. | [Launcher](../../tools/pc/start-viewer.ps1), [layout](../../tools/pc/foxglove-layout.json), [viewer instructions](../../tools/pc/README.md) |
| Sampled local scene descriptions | Ollama `qwen2.5vl:7b` describes selected frames on the PC; analysis uses the newest available frame and displays the exact analyzed frame. Observation questions can be supplied with `--task`. | [Analysis pipeline](../../tools/pc/camera_analysis.py), [inference evidence and limitations](../../tools/pc/README.md) |
| Detector boxes and confidence | CPU YOLO11s provides original-image pixel boxes, labels and confidence for common COCO classes; overlays use detector coordinates. | [Detector](../../tools/pc/object_detection.py), [sample-image validation](../../tools/pc/README.md) |
| Structured model observations and response validation | Clean image paired with task, frame ID and matching detections; response validator rejects extra fields and invented object IDs. Missing geometry stays unknown. | [Observation adapter and validator](../../tools/pc/qwen_observation.py), [seven automated checks](../../tools/pc/test_qwen_observation.py) |
| Optional robot context adapter | Reads timestamped pose/map/navigation/LiDAR JSON snapshots; rejects stale, future-dated or malformed context. Real context producers are still planned. | [Context adapter](../../tools/pc/qwen_observation.py), [snapshot contract](../../tools/pc/README.md) |
| Perception inspection artifacts | Local Foxglove observation/result topics plus latest clean input, analyzed image, JSON and logs under ignored `runtime/`. | [PC pipeline](../../tools/pc/camera_analysis.py), [artifact instructions](../../tools/pc/README.md) |

## Outstanding validation and integration

These checks apply to existing implementations. Features requiring new code or
hardware are in the next section.

| Check | Remaining work |
| --- | --- |
| Profile-driven Pi deployment | Install updated package/profile and verify the camera/video services on the Pi; existing camera evidence predates the profile migration. |
| Pi boot and stream recovery | Reboot and verify all three services deliver frames; exercise disconnect/reconnect and inspect the earlier topic-advertisement-without-frames issue. |
| Foxglove GUI | Confirm sign-in, layout import, topic selection and visible live/analyzed panel rendering. |
| Latest perception pipeline on live video | Validate the YOLO and structured Qwen revisions together on the live rover feed; the Pi was unreachable during those updates. Sample-image checks and an earlier real-frame inference are recorded. |
| Camera-to-screen latency | Measure visible end-to-end delay. Current fps/bitrate measurements establish throughput only; packet timestamps are PC reception times. |
| Model and detector performance | Evaluate representative rover images, lighting, blur, warm/cold latency and task accuracy on the deployment PC; select the final model/runtime. The Qwen3-VL research candidate has not replaced the running Qwen2.5-VL prototype. |

See the [PC viewer README](../../tools/pc/README.md) and
[commissioning log](../archive/COMMISSIONING_2026-10-11.md) for existing evidence
and operating constraints.

## Still to implement or commission

All items below are planned. Architecture diagrams and proposed interfaces are
design documentation, not evidence that the corresponding runtime exists.

| Area | Remaining features / acceptance work | Design reference |
| --- | --- | --- |
| LD06 LiDAR | Verify wiring, power and serial path; select/install the real ROS driver; configure and enable the adapter; verify `/scan` units, timing, QoS and `lidar_link` mounting transform. | [Hardware stack and swap procedure](../hardware/HARDWARE_STACK.md) |
| Chassis, UART and mobile power | Receive and identify the ESP32/driver board; verify firmware, pins, electrical levels and protocol; configure the UART; validate batteries and the Pi supply under load. | [Commissioning plan](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md) |
| ROS base driver and telemetry | Implement Pi ROS-to-JSON UART bridge, status parsing and bounded velocity output against the verified factory firmware. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Motion safety and control ownership | Implement Pi command mux/safety gate, manual/autonomy ownership, bounds, command expiry, watchdogs and fault stops; verify communication-loss behavior and the independent physical stop path before floor tests. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Movement, encoders, odometry and TF | Validate wheels-raised motion and feedback; establish odometry/transform ownership and measured behavior before low-speed floor testing. | [Base commissioning](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#commission-the-esp32-base) |
| Onboard IMU and fused odometry | Publish the documented ICM-20948 telemetry through the base adapter; verify units, axes, bias, timing and orientation availability; fuse verified wheel/IMU measurements on the Pi. | [UGV02 telemetry findings](../hardware/UGV02_BASE_TELEMETRY.md) |
| PC-to-Pi control transport | Select the Windows manual-input/task-action path; define interfaces and test leases, cancellation, QoS and link loss. Current visualization uses WebSockets/SSH with Pi DDS scoped to localhost. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md), [commissioning network notes](../archive/COMMISSIONING_2026-10-11.md#persistent-video-and-pc-analysis-setup-2026-10-11) |
| Calibrated and localized perception | Calibrate camera intrinsics; implement sensor timing/association, camera-to-robot/map transforms and validated range/position estimates. Persistent object tracking is not implemented. | [Perception and semantic map design](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md) |
| Bounded robot actions | Implement actions such as rotate, stop/cancel, scan and navigation with parameter validation, deadlines, feedback and defined failures. | [Bounded robot actions](../architecture/ROS_ARCHITECTURE.md#command-authority-and-bounded-robot-actions) |
| Mission executive and model tools | Implement deterministic task state, allowlisted model skill proposals, execution, cancellation, bounded retries/recovery and decision-event logging. The current model only reports observations. | [Command and action authority](../architecture/ROS_ARCHITECTURE.md#command-authority-and-bounded-robot-actions), [model tools](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md#persistent-object-memory-and-model-tools) |
| PC operator application | Build joystick teleoperation, conversational task input, camera/robot/task status, control ownership and a task-focused 2D map. Foxglove is the current development viewer. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Mapping, localization and navigation | Commission the selected sensor inputs; evaluate SLAM Toolbox, Nav2 and fusion configuration on the Pi; persist Pi-owned geometric maps and pose; verify navigation independently before connecting model tasks. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Semantic map and robot context producers | Implement versioned room/landmark/object annotations, evidence validation, Pi persistence and PC backup; supply real pose/map/navigation/sensor context to perception. | [Perception and semantic map design](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md) |
| Two-stage PC object memory | Separate detector/model workers; source-time image/context transport; saved crops/full frames; candidate sightings, measured grounding where available, asynchronous semantic enrichment and bounded model map queries. Design recorded; runtime not implemented. | [Perception and semantic map design](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md) |
| Autonomous discovery and object search | Implement bounded safe viewpoint exploration, room discovery, saved semantic destinations and object search; escalate after recovery limits or health/safety faults. Object approach depends on validated geometry and navigation. | [Perception and semantic map design](../architecture/PERCEPTION_AND_SEMANTIC_MAP.md) |
| Larger utility rover | Adapt the stable base abstraction to a stronger drivetrain, battery, steering, hauling/towing hardware and independent safety systems. Deferred beyond the small prototype. | [Future rover scope](PROJECT_NOTES.md#future-large-rover-scope) |

## Suggested next sequence

This is the single project build order. Subsystem documents describe their own
acceptance checks; they do not maintain competing project roadmaps.

1. Apply/verify the profile-driven camera deployment and finish video/viewer
   recovery checks. Keep calibration and source-timestamp transport work visible.
2. Commission the base, UART and power; implement the Pi serial adapter and local
   command gate. Verify manual low-speed control, expiry, faults and stopping
   with wheels raised before floor tests.
3. Commission onboard encoder/IMU feedback, LD06, sensor mounts and camera
   calibration. Establish repeatable Pi odometry, mapping/localization and map
   persistence from real sensor data.
4. Validate local navigation to ordinary poses and the PC-to-Pi bounded task,
   cancellation and feedback interface before attaching model-selected goals.
5. Integrate source-time observations, candidate sightings, curated evidence,
   semantic queries and asynchronous enrichment; add verified object grounding
   and committed viewer map layers.
6. Add model-driven inspection/search, saved semantic destinations and the
   task-focused operator app on top of those validated interfaces.

PC worker separation and image-only object-memory development can proceed in
parallel with hardware bring-up. Unlocalized sightings and recorded fixtures
are useful development inputs, but do not pass physical grounding/navigation
acceptance. Basic operator controls support bring-up; the full task app follows
working action/map interfaces.

## Keeping this list current

Update this file when a capability lands or a commissioning check passes. Move
implemented work out of the planned table, link its code and recorded evidence,
and keep any remaining acceptance checks explicit. Update the review date. Keep
detailed procedures and historical measurements in their existing documents;
use this page as the current feature summary.
