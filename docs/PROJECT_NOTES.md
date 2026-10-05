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

See [ROS_ARCHITECTURE.md](ROS_ARCHITECTURE.md) for the node graph, topic direction, command ownership, safety boundaries, and system diagrams. The Pi's command mux/safety gate is the sole authority for selecting and validating motion requests before the base driver; model and planner outputs never command motors directly.

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
- Use ordinary Pi camera support and a ROS camera driver rather than legacy camera utilities.
- Prefer a clean hardware abstraction so the robot base can later be swapped without rewriting the autonomy model interface.
- Keep semantic model decisions separate from low-level drive and safety control.
- Build a PC operator application as an explicit project feature, with conversational task input, joystick teleoperation, a 2D map with semantic annotations, and camera/robot/task status.
- Keep the model and task planning on the PC; the Pi receives bounded robot actions and retains local command validation and safe-stop authority.
- Let the Pi mapping/localization stack own the geometric map and robot pose. Let the PC multimodal model propose room/landmark/object annotations from selected camera observations; validate and store these in a versioned semantic map layer on the Pi, with a PC backup.
- Treat Foxglove Studio as an optional ROS visualization and diagnostics tool, not as the required operator application.
- Use one local multimodal model on the PC for conversation, image interpretation, and proposing allowlisted skills. The detected PC GPU is an NVIDIA RTX 2080 Ti with 11 GiB VRAM; start by benchmarking a supported 4-bit Qwen3-VL Instruct 4B configuration. Keep deterministic mission logic, ROS navigation, robot drivers, and Pi safety controls as ordinary software, not additional models. See [ACTION_MODEL_RESEARCH.md](ACTION_MODEL_RESEARCH.md) for the model assessment.
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
4. Choose an OS and ROS distribution combination with reproducible installation steps.
5. Connect the Pi camera stack and verify image publishing.
6. Add the Waveshare ROS driver or adapter layer.
7. Bring up basic low-level motion and odometry tests with wheels elevated.
8. Develop command freshness, watchdog, and safe-stop behavior.
9. Add camera-first experiments and localisation trials.
10. Preserve a stable robot abstraction for future large-cart hardware.
11. Define the operator-app-to-mission and mission-to-robot interfaces, including bounded actions, feedback, cancellation, and faults.
12. Build the PC operator application with joystick control, a task-focused 2D map, camera/task/robot status, and explicit manual/autonomy ownership; keep it out of the initial hardware commissioning critical path. Use Foxglove during bring-up to inspect raw ROS data rather than making it the operator app.
13. Add conversational task input through one local PC-side multimodal model. Benchmark Qwen3-VL Instruct 4B with a supported 4-bit runtime on the RTX 2080 Ti; test a smaller checkpoint if memory or latency is inadequate. Test simple actions before visual search tasks. Confirm usable memory, end-to-end latency, and accuracy on the actual camera stream before fixing the deployment configuration.
14. Select and validate the mapping/localization sensor stack. Establish Pi-owned geometric map persistence and a separate semantic annotation layer that can be proposed by the PC model and committed through a validated ROS interface.
15. Implement autonomous semantic discovery over the validated map/localization stack, including bounded viewpoint search, evidence-based annotation updates, recovery limits, and failure-only operator escalation.

## Unknowns that need explicit handling

- ROS distribution and OS pinning
- Camera driver and libcamera compatibility
- Whether a custom ROS adapter is needed for the actual Waveshare protocol
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
