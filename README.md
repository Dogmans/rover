# Rover project

This repository is being initialized around the rover concept captured in the project handoff.

## Mission

Build a useful outdoor rover capable of hauling and towing garden implements, starting with a smaller, indoor-friendly prototype based on the Waveshare UGV02 chassis and a ROS 2 software stack.

## Current direction

- Use a small purchased rover base for platform development
- Run ROS 2 on a Raspberry Pi 5
- Use the onboard Waveshare ESP32 controller via its serial interface
- Keep the PC in the loop for perception and higher-level autonomy
- Preserve a clean hardware abstraction so the large rover can later replace the base driver without rewriting the model interface

## Key constraints

- Treat the handoff as planning context, not as a verified hardware configuration
- Confirm board revision, power budget, camera, cables, enclosure, and firmware before finalizing installation
- Prefer reproducible ROS 2 setup and open-source tooling over bespoke base control logic
- Keep safety and command freshness explicit in the control path

## Project notes

See [docs/PROJECT_NOTES.md](docs/PROJECT_NOTES.md) for the detailed implementation intent and next actions.

## Setup plan

- [docs/ROS_ARCHITECTURE.md](docs/ROS_ARCHITECTURE.md) — ROS nodes, command/data flows, ownership, and failure behavior
- [docs/PI5_ROS_ESP32_SETUP_PLAN.md](docs/PI5_ROS_ESP32_SETUP_PLAN.md) — step-by-step Pi 5, ROS 2, and ESP32 commissioning plan
- [docs/EXTERNAL_REFERENCES.md](docs/EXTERNAL_REFERENCES.md) — the vendor and platform references that informed the plan
