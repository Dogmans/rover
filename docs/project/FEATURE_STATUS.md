# Feature status

Last reviewed: 2026-10-12.

This is the central checklist of implemented capabilities and remaining work. It
summarizes repository code and recorded commissioning results; it is not a fresh
live-hardware test. The [project notes](PROJECT_NOTES.md) explain the goals and
design decisions, the [ROS architecture](../architecture/ROS_ARCHITECTURE.md)
describes the target system, and the
[commissioning plan](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md) records bring-up evidence.

The working baseline is camera streaming and sampled local scene analysis. The
ESP32 has not arrived according to the latest commissioning record, so motor
control and autonomous operation remain unimplemented.

## Implemented

Implemented means code or a commissioned component exists. Validation limits are
listed separately below; these entries do not imply readiness for autonomous use.

| Feature | Current capability | Evidence / implementation |
| --- | --- | --- |
| Pi OS and ROS runtime | Ubuntu Server 24.04 ARM64 and ROS 2 Jazzy installed on the commissioned Pi. | [Commissioning results](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#observed-commissioning-result-2026-10-11) |
| Hardware profile and replaceable sensor adapters | Versioned hardware selection, shared ROS topic contracts and profile-driven camera launcher; generic ROS LaserScan adapter and optional disabled LiDAR service. Repository implementation; updated deployment not yet verified on the Pi. | [Hardware stack](../hardware/HARDWARE_STACK.md), [Pi adapters](../../deploy/pi/rover_hardware/), [hardware profile](../../config/hardware/ugv02-pi5.json) |
| CSI camera capture and ROS publication | Camera Module 3 Wide still/video capture verified; raw images and uncalibrated CameraInfo published at approximately 30 Hz. | [Camera commissioning](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#observed-commissioning-result-2026-10-11), [camera launcher](../../deploy/pi/rover-camera.sh) |
| Persistent Pi camera and bridge services | Versioned systemd units and installer; camera, Foxglove bridge and video encoder enabled at boot. | [Deployment installer](../../deploy/pi/install-visualization.sh), [service commissioning](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#persistent-video-and-pc-analysis-setup-2026-10-11) |
| Pi ROS observability bridge | Foxglove WebSocket bridge exposes camera topics and diagnostics on the trusted LAN. | [Bridge launcher](../../deploy/pi/rover-foxglove.sh), [bridge check](../../deploy/pi/check-foxglove.ps1) |
| H.264 video transport to PC | 1280x720 at 20 fps over an SSH tunnel; measured approximately 20 decoded fps at 2 Mbps. Single PC receiver; receiver retry and encoder restart behavior implemented. | [Pi encoder](../../deploy/pi/rover-video.py), [PC receiver](../../tools/pc/camera_analysis.py), [transport evidence](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#video-transport-revision-2026-10-11) |
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
[commissioning log](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md) for existing evidence
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
| Movement, encoders, odometry and TF | Validate wheels-raised motion and feedback; establish odometry/transform ownership and measured behavior before low-speed floor testing. | [Integration milestones](../architecture/ROS_ARCHITECTURE.md#first-integration-milestones) |
| PC-to-Pi ROS command network | Define interfaces and test discovery, QoS, command freshness and network loss. Current visualization uses WebSockets/SSH with Pi DDS scoped to localhost. | [ROS architecture](../architecture/ROS_ARCHITECTURE.md), [commissioning network notes](../hardware/PI5_ROS_ESP32_SETUP_PLAN.md#persistent-video-and-pc-analysis-setup-2026-10-11) |
| Calibrated and localized perception | Calibrate camera intrinsics; implement sensor timing/association, camera-to-robot/map transforms and validated range/position estimates. Persistent object tracking is not implemented. | [Action model research](../research/ACTION_MODEL_RESEARCH.md#proposed-action-boundary) |
| Bounded robot actions | Implement actions such as rotate, stop/cancel, scan and navigation with parameter validation, deadlines, feedback and defined failures. | [Proposed action boundary](../research/ACTION_MODEL_RESEARCH.md#proposed-action-boundary) |
| Mission executive and model tools | Implement deterministic task state, allowlisted model skill proposals, execution, cancellation, bounded retries/recovery and decision-event logging. The current model only reports observations. | [Action model research](../research/ACTION_MODEL_RESEARCH.md) |
| PC operator application | Build joystick teleoperation, conversational task input, camera/robot/task status, control ownership and a task-focused 2D map. Foxglove is the current development viewer. | [Project notes](PROJECT_NOTES.md#software) |
| Mapping, localization and navigation | Select and validate sensors and SLAM/localization stack; persist Pi-owned geometric maps and pose; verify navigation independently before connecting model tasks. | [Project notes](PROJECT_NOTES.md#initial-implementation-plan), [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Semantic map and robot context producers | Implement versioned room/landmark/object annotations, evidence validation, Pi persistence and PC backup; supply real pose/map/navigation/sensor context to perception. | [Project notes](PROJECT_NOTES.md#software), [ROS architecture](../architecture/ROS_ARCHITECTURE.md) |
| Autonomous discovery and object search | Implement bounded safe viewpoint exploration, room discovery, saved semantic destinations and object search; escalate after recovery limits or health/safety faults. Object approach depends on validated geometry and navigation. | [Action model research](../research/ACTION_MODEL_RESEARCH.md), [project notes](PROJECT_NOTES.md#initial-implementation-plan) |
| Larger utility rover | Adapt the stable base abstraction to a stronger drivetrain, battery, steering, hauling/towing hardware and independent safety systems. Deferred beyond the small prototype. | [Future rover scope](PROJECT_NOTES.md#future-large-rover-scope) |

## Suggested next sequence

1. Finish the existing camera/viewer/perception acceptance checks above.
2. Commission the delivered chassis, UART and power system.
3. Implement the base driver and Pi safety gate; verify stop/fault behavior and
   odometry with wheels raised before floor tests.
4. Add bounded actions, the mission executive and operator controls.
5. Establish calibration, mapping/localization and independently tested navigation.
6. Add semantic maps, conversational missions and autonomous discovery/search.

## Keeping this list current

Update this file when a capability lands or a commissioning check passes. Move
implemented work out of the planned table, link its code and recorded evidence,
and keep any remaining acceptance checks explicit. Update the review date. Keep
detailed procedures and historical measurements in their existing documents;
use this page as the current feature summary.
