# Rover project notes

This document captures the implementation direction from the handoff and is intended to be a practical starting point for the next agent or coding session.

## Goal

Create a capable outdoor rover platform with a staged development path:

1. Start with a small, purchased chassis to develop software and integration indoors and outdoors.
2. Validate sensing, control, networking, and camera-first autonomy on the small platform.
3. Later adapt the same software and interfaces to a larger utility/cart-style rover with stronger motors, battery, steering, and safety hardware.

## Architecture target

- Remote PC: operator application, model inference, perception, planning, and higher-level action selection
- ROS 2 over Wi-Fi: command, status, and telemetry transport between PC and robot
- Raspberry Pi 5: onboard controller and ROS 2 host
- Waveshare ESP32 board: low-level motor control, encoders, and chassis interface
- Camera: Raspberry Pi Camera Module 3 Wide via Pi camera stack

See [ROS_ARCHITECTURE.md](../architecture/ROS_ARCHITECTURE.md) for the node graph, topic direction, command ownership, safety boundaries, and system diagrams. The Pi's command mux/safety gate is the sole authority for selecting and validating motion requests before the base driver; model and planner outputs never command motors directly.

## Product and hardware assumptions

The handoff explicitly notes that several facts are still unresolved and must be rechecked on the actual hardware:

- Waveshare board revision and firmware variant
- Whether the chassis is using the ROS Driver or General Driver variant
- UART wiring, protocol, pinout, and watchdog/timeout behavior
- Pi 5 power budget and whether additional regulation is needed
- Camera cable, microSD card, active cooler, and other support parts
- Exact encoder availability and odometry semantics
- Battery and charging configuration for the small rover base

These are not to be assumed settled without fresh validation.

## Current design direction

### Hardware

- Use the Waveshare UGV02 6x4 rover as the initial development robot.
- Keep the ESP32 firmware in place initially unless a real compatibility issue demands changes.
- Avoid making the Waveshare browser app or a custom application a prerequisite for commissioning.
- Use UART as the Pi-to-ESP32 host interface, with the correct protocol revision for the board being used.

### Software

- Prefer ROS 2 on a Pi-based robot stack.
- Use Ubuntu Server 24.04 ARM64 + ROS 2 Jazzy as the default Pi baseline. Make CSI Camera Module 3 capture and ROS image publishing an early acceptance gate; change OS strategy only if that test fails on the delivered Pi/camera.
- Use ordinary Pi camera support and a ROS camera driver rather than legacy camera utilities.
- Treat Waveshare's `ugv_base_ros` repository as ESP32 firmware, not a ROS 2 host driver. Keep factory firmware and implement a small Pi-side ROS/JSON UART bridge for the delivered board.
- Prefer a clean hardware abstraction so the robot base can later be swapped without rewriting the autonomy model interface.
- Keep semantic model decisions separate from low-level drive and safety control.
- Build a PC operator application as an explicit project feature, with conversational task input, joystick teleoperation, a 2D map with semantic annotations, and camera/robot/task status.
- Keep the model and task planning on the PC; the Pi receives bounded robot actions and retains local command validation and safe-stop authority.
- Let the Pi mapping/localization stack own the geometric map and robot pose. Let the PC multimodal model propose room/landmark/object annotations from selected camera observations; validate and store these in a versioned semantic map layer on the Pi, with a PC backup.
- Use Foxglove Studio early as the optional-at-runtime development observability console for camera images and perception overlays, ROS topics, transforms, plots, diagnostics, and model/mission events. Keep the operator app task-focused; do not duplicate rich debugging views unless operational testing shows a clear need.
- Publish detections and model/mission decision events as timestamped, structured ROS data for Foxglove to inspect. Expose concise evidence/rationale summaries, not private chain-of-thought; the model remains outside the motor and safety authority path.
- Use one local multimodal model on the PC for conversation, image interpretation, and proposing allowlisted skills. Select and benchmark it on the actual target PC; the local development machine is only one hardware profile ([details](../hardware/DEVELOPMENT_PC_PROFILE.md)). Keep deterministic mission logic, ROS navigation, robot drivers, and Pi safety controls as ordinary software, not additional models. See [ACTION_MODEL_RESEARCH.md](../research/ACTION_MODEL_RESEARCH.md) for the model assessment.
- Target autonomous map building and semantic discovery: the PC model supervises bounded search and proposes room/landmark annotations; the Pi mapping/navigation stack owns geometry and movement. Escalate to the operator only when bounded search/recovery fails or safety/health requires intervention. Attended commissioning is a temporary hardware-validation precaution, not routine teleoperation.

### Control and autonomy

- Model outputs should not directly command motors.
- Use bounded, timestamped, fresh control commands and command expiry.
- Have explicit manual/automatic ownership and a safe-stop path.
- Validate wheel encoders and odometry, but do not assume they replace a full localisation stack.
- Treat visual perception, calibration, and camera-based navigation as an early goal rather than a late afterthought.

## Initial implementation plan

1. Verify physical hardware and board revision.
2. Confirm the robot interface protocol and UART connection.
3. Validate power delivery to the Pi and onboard controller under load.
4. Install Ubuntu Server 24.04 ARM64 + ROS 2 Jazzy; verify the CSI camera path before building higher-level software.
5. Connect the Pi camera stack and verify image publishing.
6. Add a minimal Pi-side UART/JSON ROS bridge; retain the factory ESP32 firmware unless the delivered unit forces a change.
7. Bring up basic low-level motion and odometry tests with wheels elevated.
8. Develop command freshness, watchdog, and safe-stop behavior.
9. Add camera-first experiments and localisation trials.
10. Preserve a stable robot abstraction for future large-cart hardware.
11. Define the operator-app-to-mission and mission-to-robot interfaces, including bounded actions, feedback, cancellation, and faults.
12. Use Foxglove during bring-up to inspect camera images with timestamp-aligned detection annotations, ROS data, and structured model/mission decision events. Keep the PC operator application focused on joystick control, a task-focused 2D map, camera/task/robot status, and explicit manual/autonomy ownership; do not make it a second debugging dashboard or a commissioning prerequisite.
13. Add conversational task input through one local PC-side multimodal model. Benchmark candidates on the actual deployment PC; Qwen3-VL Instruct 4B with supported 4-bit quantization is an initial candidate for the recorded development PC, not a fixed project requirement. Test smaller checkpoints if memory or latency is inadequate. Test simple actions before visual search tasks and confirm end-to-end latency and accuracy on the actual camera stream before fixing a deployment configuration.
14. Select and validate the mapping/localization sensor stack. Establish Pi-owned geometric map persistence and a separate semantic annotation layer that can be proposed by the PC model and committed through a validated ROS interface.
15. Implement autonomous semantic discovery over the validated map/localization stack, including bounded viewpoint search, evidence-based annotation updates, recovery limits, and failure-only operator escalation.

## Unknowns that need explicit handling

- Camera driver and libcamera compatibility on Ubuntu 24.04; this remains an early acceptance gate
- Exact Pi-side bridge package, message contract, and ROS package versions
- Whether the current firmware exposes odometry and motor-safety behavior as expected
- Wi-Fi quality, QoS, and ROS discovery configuration on the local network
- Operator application platform/framework and its connection to PC-side ROS nodes
- Model serving runtime, quantization, and measured latency/accuracy for local vision-language inference
- Mapping/localization method and sensor requirements; semantic-map record format and update/confirmation policy
- Future large rover steering and drivetrain architecture

## Success criteria for the prototype

- Basic robot movement under ROS 2 is reliable and testable
- The Pi can receive and publish status, camera feed, and motion commands
- Safety checks and command freshness are enforced
- A PC operator application can control the rover manually and submit conversational tasks through bounded robot actions
- The operator app can display the current geometric map, robot pose, semantic room annotations, active destination/path, and task state from the Pi's map/navigation interfaces
- Camera-first experiments are possible without a large sensor stack
- The robot abstraction remains stable for later hardware replacement

## Future large rover scope

This is deferred but remains the eventual objective:

- 24 V utility platform
- stronger motors and drive hardware
- trailer/implement hauling capability
- safety systems isolated from model or compute tasks
- a hardwired E-stop and motor removal path independent from software

The current small rover is a development platform, not the final delivery vehicle.
