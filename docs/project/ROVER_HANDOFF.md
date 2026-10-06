# Rover project — configuration and planning handoff

Updated: 4 October 2026. This captures decisions from a discussion, not a tested configuration. Use this as context for a VS Code coding agent to produce a detailed implementation plan. Do not treat proposed OS choices or unverified hardware specifications as settled.

## Goal and current direction

Build a serious mechanical/electronics/controls/autonomy/physical-AI project, eventually a useful outdoor rover capable of hauling and towing garden implements. Start with a small purchased robot to develop software indoors and outdoors before building the full-size utility cart.

Current architecture: remote PC action/perception model → ROS 2 over Wi-Fi → Raspberry Pi 5 → onboard UART → Waveshare ESP32 controller → motor drivers/motors. Camera images and robot status travel back to the PC.

The user wants to go straight to ROS 2. Do not make Waveshare's browser application a prerequisite or a separate prolonged development stage. Hardware commissioning can take place through the ROS stack.

## Hardware inventory

| Item | Status | Details |
| --- | --- | --- |
| Waveshare UGV02 6x4 chassis | Ordered | User ordered following discussion of The Pi Hut listing below. Confirm actual order/SKU and board when delivered. Listing SKU WAV-25077, £144 at time checked. Six wheels, outer four powered; independent left/right drive. |
| Raspberry Pi 5 | Ordered | RAM size was not explicitly confirmed. Recommended 4 GB, but do not assume ordered capacity. |
| Official Raspberry Pi Camera Module 3 Wide | Ordered | Pi Hut variant 42305752072387, SKU SC1224; Sony IMX708, autofocus, about 102° horizontal / 120° diagonal FoV. Standard colour/IR-cut version, not NoIR. Fixed mount initially; no pan/tilt required. |
| 18650 lithium-ion cells | Already owned | User has many. Select three matching suitable cells after checking discharge rating, condition, dimensions and terminal style. |
| Remote PC with NVIDIA RTX GPU | Already available | Intended for expensive model inference over Wi-Fi. Exact current GPU/VRAM, OS and model are not confirmed in this discussion. Ask/check locally rather than assume. |
| Linear actuators | Already owned | Possible future cart steering; models, feedback, speed, stroke and force unknown. |
| Pi 5 camera cable | Unconfirmed | Wide camera package explicitly excludes Pi 5 cable. Needs 22-pin Pi-side to 15-pin camera-side CSI camera cable. |
| MicroSD | Unconfirmed | 32–64 GB recommended; not a confirmed purchase. |
| Pi 5 active cooler | Unconfirmed | Recommended; check clearance around chassis/header. |

### Chassis and power details from retailer

The Pi Hut says current stock uses the newer **ROS Driver for Robots** internal board. Older UGV02 units used **General Driver for Robots**. Confirm the printed board identity before selecting firmware or pin assignments.

Listing states: assembled chassis, UK 12.6 V/2 A charging power supply, USB cable, mounting plate, camera holder and accessories. Pi, camera and three 18650 cells are separate. Nominal chassis dimensions 252 × 230 × 94 mm, approx. 2 kg, 80 mm wheels, advertised moving payload 4 kg, 4 × 5 W motors. These are advertised values, not independently tested performance.

Three cells in series: approx. 11.1 V nominal / 12.6 V fully charged. Three 3000 mAh cells give 3000 mAh pack capacity and approx. 33 Wh, not 9000 mAh. Onboard circuitry handles charging/protection; supplied adapter is not the Pi's mains supply.

The fitted board exposes UART/I2C on its 40-pin header; it does not expose general-purpose GPIO through that header. Verify the exact pinout and electrical levels against the delivered board before connecting the Pi. Waveshare documents 5 V and 3.3 V expansion outputs but does not give a verified continuous 5 V current rating adequate for a Pi 5. Power the Pi from a known 5 V/5 A source during bench bring-up; do not power it from the rover board until its rating is confirmed.

**Power decision:** Treat the rover board's 5 V output as unqualified for Pi 5 power. Use a separate regulated 5 V supply with adequate current for the Pi during development, and test the final battery-to-Pi regulator under CPU, camera and motor load. Do not parallel supplies or backfeed the Pi.

## Controller and firmware

The ESP32 handles low-level motor control, encoder processing and onboard sensors. Retain factory firmware initially. Its documented host interface is JSON via GPIO UART or USB serial at 115200 baud. **The board name “ROS Driver” does not mean it communicates natively using ROS or micro-ROS.** A Pi-side ROS driver/adapter translates between ROS and the serial protocol.

The current UGV02 documentation identifies firmware version 0.96 and the official `ugv_base_ros` repository as the ESP32 firmware for the newer ROS Driver board; the older UGV02 General Driver requires `ugv_base_general`. Despite its name, `ugv_base_ros` is ESP32 firmware, not a ROS 2 host package. Use the factory firmware initially and implement a small Pi-side ROS-to-JSON serial bridge unless the delivered board/firmware proves incompatible.

Encoder-equipped UGV02 documentation exists, and the newer firmware advertises closed-loop PID. Still verify actual motor encoders, which channels are connected, feedback units and odometry availability on the delivered kit. The cheaper **WAVE ROVER** is a different model with no motor encoders; its “speed” commands are PWM fractions. Do not import that limitation or protocol interpretation blindly into UGV02.

The current UGV02 reference documents newline-delimited JSON over UART/USB at 115200 baud; `T=13` accepts linear velocity `X` in m/s and angular velocity `Z` in rad/s. `T=1` accepts left/right wheel speeds in m/s (documented range -0.5 to +0.5). `T=130` requests base feedback, and `T=131,cmd=1` enables continuous feedback. The current firmware source sets a 3000 ms heartbeat timeout; treat that only as a secondary firmware stop and verify it on the delivered unit. The documented geometry defaults are 80 mm wheel diameter and 172 mm track width; calibrate encoder scale and effective track width on the actual chassis before using odometry.

The vendor source reads one encoder channel per side (front-wheel feedback); it does not provide independent feedback for all four driven wheels. Treat odometry as provisional and validate direction, ticks-per-distance, and slip before using it for navigation.

No additional Pico 2, Pixhawk or motor driver is needed for the small platform's initial operation. A Pi + Pico 2 + Linorobot2 was considered for a custom robot but superseded by using the purchased Waveshare base.

## OS / ROS decisions

**Settled:** ROS 2 on Pi; model on PC; ordinary Pi camera stack; use Waveshare's ESP32 interface rather than its entire Pi application.

**Default software decision (not yet hardware-validated):** use Ubuntu Server 24.04 ARM64 with ROS 2 Jazzy on the Pi, and keep the model/operator application on the PC. This is the cleanest supported ROS binary-package path for Pi 5. Make CSI camera capture on the exact Camera Module 3 Wide an early acceptance gate before investing in higher-level software; if the native camera path is not reliable on Ubuntu, stop and select a Raspberry Pi OS-based ROS deployment deliberately rather than layering workarounds into the baseline. No image has been installed or validated yet.

The Pi camera uses the modern libcamera/rpicam stack, not legacy raspistill/raspivid. Raspberry Pi documents IMX708 support, but validate camera capture and ROS image publication on the selected Ubuntu image before treating the full stack as proven. Waveshare's Pi application is not a prerequisite and `ugv_base_ros` is the lower-computer firmware, not a ready ROS 2 host driver. No applicable turnkey UGV02/Pi 5 ROS 2 image was confirmed.

The Pi camera uses modern libcamera/rpicam/Picamera2 paths, not legacy raspistill/raspivid and not automatically a generic USB webcam node. Ubuntu 24.04 + ROS 2 Jazzy is the Pi baseline, with CSI capture and ROS image publication as an early acceptance gate. Publish timestamped images and CameraInfo; calibrate the wide lens for geometric vision.

## Remote intelligence and autonomy

PC model may perform semantic interpretation, scene understanding, action selection and possibly perception/localisation/planning. Pi need not understand “shed”: PC can identify it and send a mapped target position/heading, or use a previously configured named destination.

Recognising an object in pixels does not establish a reachable ground/map coordinate. Plan calibrated house-camera tracking, onboard visual localisation or known markers/map anchors as appropriate. Camera-based navigation is the user's preferred direction; GNSS is not the default initial dependency. Indoor tests are viable once localisation exists.

Keep separate:

- Semantic model decisions.
- Conventional localisation, navigation, obstacle checks and command arbitration.
- ESP32 deterministic wheel control.
- Independent physical propulsion isolation on the eventual large rover.

Model outputs must pass through bounded conventional control, not unrestricted motor PWM. For experiments, short-lived motion requests may be generated remotely, but PC/model latency and Wi-Fi loss must not cause continued stale movement. Use timestamps/expiry, command freshness, explicit manual/automatic ownership and safe stop behaviour. Pi re-publishing an old command must not defeat the ESP32 timeout.

Use ROS 2 directly over the LAN between PC and Pi; separate HTTP service is optional, not required. Establish compatible message types, ROS_DOMAIN_ID, DDS discovery/network settings and QoS. Network environment and PC OS are still unknown. Do not stream full-resolution raw video blindly over Wi-Fi; choose suitable compressed transport, resolution/frame rate, bounded buffering and measured end-to-end latency.

Wheel encoders remain valuable for speed control and short-term odometry even with skid steering. Odometry alone is unreliable under slip; fuse/compare with IMU and visual position. Do not confuse controlled wheel RPM with controlled ground velocity.

## UI

The project PC operator application is an explicit feature: conversational task requests, joystick teleoperation, a task-focused 2D map with semantic annotations, and camera/robot/task status, backed by PC-side model and mission components. Its framework and exact ROS-facing interfaces remain open. Foxglove is recommended as an optional bring-up/diagnostics dashboard for raw video, pose/map, status, plots, and ROS inspection; it is not the required chat or operator app. Verify current compatibility/licensing before selecting. Neither the app, a dashboard, nor a network stop button is an independent E-stop.

## Full-size rover — future scope, not purchased

Original concept: 40–60 kg, 700–800 mm wide, 24 V, pneumatic tyres, two geared brushed wheelchair motors preferably with quadrature encoders. Initial useful rover budget approx. £1,000–£2,000.

A garden trolley is now a serious donor-chassis option: power the fixed axle/end and use the original swivelling axle at the opposite end as passive support. A swivelling axle is not automatically a self-aligning caster: inspect pivot/contact-patch geometry. Removable straight-ahead lock was proposed for initial tests; turns then cause lateral tyre scrub. Reverse behaviour, steering limits and stability need mechanical testing. Actuator steering remains an option. No mechanical differential required with independent drive motors.

Oypla donor example is linked below; cheap frame/axle quality may require reinforced motor crossmember and hitch structure. Not ordered/owned based on this conversation.

Earlier candidate electronics: Holybro Pixhawk 6C/ArduRover, Sabertooth 2x32, ZED-F9P RTK with NTRIP, 24 V LiFePO4 eventually around 50 Ah. **All deferred/provisional, not purchased or required by the current small prototype.** Motor driver and battery selection follow actual motors, continuous/stall current, torque/gearing and braking requirements. ArduPilot remains a future option, including external camera navigation; current direction is ROS + MCU.

Future hitch: structural rear hitch, auxiliary 24 V, data (CAN/RS485 considered) and safety-loop connection. First useful attachments: trailer/hauling. Powered mower only after substantial vehicle/autonomy testing, with separate independently interlocked implement power. AI must not own safety-critical functions. Large rover needs hardwired E-stop/relay/contactor removing propulsion power independently of Pi/MCU, and braking evaluated separately from power removal.

## Requested next-agent deliverable

Produce a detailed practical implementation plan grounded in the delivered hardware and official source code:

1. Verify board revision, encoder feedback, UART pinout/protocol and Pi power budget.
2. Validate the Ubuntu 24.04/Jazzy baseline with the CSI camera and record exact image/package versions; pivot only if the camera acceptance gate fails.
3. Confirm the delivered board/firmware variant and implement the minimal Pi-side serial bridge for the documented JSON protocol; test the 3-second firmware timeout as a backup, not the primary command watchdog.
4. Define ROS nodes, topics/actions, frames, camera transport, localisation options and model-to-autonomy interface. Avoid duplicate differential-drive/odometry implementations.
5. Plan PC environment and LAN setup, manual/automatic arbitration, fresh-command checks and failure recovery.
6. Commission with wheels elevated, then low-speed floor tests: direction, encoder scaling, stopping, network loss, process crash, reset, power dips and camera loss.
7. Establish useful camera-first experiments before introducing unnecessary sensors or a large autonomy stack.
8. Preserve hardware abstraction so later large-cart motor hardware replaces the base driver without rewriting the model interface.

State unresolved assumptions explicitly. Do not assume purchases of RAM capacity, cable, cooling, SD card, driver revisions or full-size components. User prefers useful progress and existing open-source software over reinventing base control.

## Official/retailer references

- Ordered chassis reference: https://thepihut.com/products/6x4-off-road-ugv-kit-esp32-driver
- Camera variant: https://thepihut.com/products/raspberry-pi-camera-module-3?variant=42305752072387
- UGV02 documentation: https://www.waveshare.com/wiki/UGV02
- Newer ESP32 firmware: https://github.com/waveshareteam/ugv_base_ros
- Older ESP32 firmware: https://github.com/waveshareteam/ugv_base_general
- Board schematic: https://files.waveshare.com/wiki/RaspRover/ROS_Driver_for_Robots.pdf
- Pi vendor examples: https://github.com/waveshareteam/ugv_rpi
- Vendor ROS kit reference: https://www.waveshare.com/wiki/UGV_Rover_PI_ROS2
- Pi camera documentation: https://www.raspberrypi.com/documentation/computers/camera_software.html
- Alternate MCU firmware considered: https://github.com/linorobot/linorobot2_hardware
- Future donor cart example: https://www.diy.com/departments/oypla-heavy-duty-metal-garden-trolley-trailer-cart-wagon-removable-sides/6166416154066_BQ.prd

References were discussed/read on 4 October 2026; recheck current content and actual hardware before implementation. No hardware has yet been commissioned in this session.
