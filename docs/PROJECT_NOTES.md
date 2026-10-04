# Rover project notes

This document captures the implementation direction from the handoff and is intended to be a practical starting point for the next agent or coding session.

## Goal

Create a capable outdoor rover platform with a staged development path:

1. Start with a small, purchased chassis to develop software and integration indoors and outdoors.
2. Validate sensing, control, networking, and camera-first autonomy on the small platform.
3. Later adapt the same software and interfaces to a larger utility/cart-style rover with stronger motors, battery, steering, and safety hardware.

## Architecture target

- Remote PC: model inference, perception, planning, and higher-level action selection
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

## Unknowns that need explicit handling

- ROS distribution and OS pinning
- Camera driver and libcamera compatibility
- Whether a custom ROS adapter is needed for the actual Waveshare protocol
- Whether the current firmware exposes odometry and motor-safety behavior as expected
- Wi-Fi quality, QoS, and ROS discovery configuration on the local network
- Future large rover steering and drivetrain architecture

## Success criteria for the prototype

- Basic robot movement under ROS 2 is reliable and testable
- The Pi can receive and publish status, camera feed, and motion commands
- Safety checks and command freshness are enforced
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
