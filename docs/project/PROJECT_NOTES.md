# Project goals and rationale

Reviewed: 2026-10-12. This document owns project purpose and scope. Current
implementation lives in [Feature status](FEATURE_STATUS.md), component decisions
in the [ROS architecture](../architecture/ROS_ARCHITECTURE.md), and selected parts
in the [hardware stack](../hardware/HARDWARE_STACK.md).

## Goal

Build a useful outdoor rover for hauling and towing garden equipment. Start
with a purchased UGV02 to develop sensing, software, controls and integration;
then transfer the stable autonomy interfaces to a larger utility vehicle.
The small chassis is a development platform, not the final hauling vehicle.

Indoor tests establish basic mapping and movement before evaluating outdoor
terrain, lighting, traction and sensor coverage. The current sensing baseline
includes a camera, selected 2D LiDAR, and onboard encoder/IMU feedback; sensor
commissioning and acceptance limits are tracked in the hardware/status documents.

## Why this approach

- Use existing ROS drivers and navigation software where they fit, with small
  project-owned adapters around hardware-specific protocols.
- Keep visual inference and task interpretation on the PC while the robot owns
  local movement, stopping and persistent map state.
- Treat geometric mapping and semantic object memory as distinct responsibilities
  so model descriptions cannot silently become invented spatial measurements.
- Preserve driver boundaries so a new sensor or drivetrain does not require
  changing the model's task vocabulary.
- Use Foxglove for development inspection. Build the eventual operator app around
  tasks, manual input and map/camera/status rather than a second general debugger.
- Develop autonomous discovery with bounded inspection and recovery. Attended
  bring-up establishes acceptance evidence; routine teleoperation is not the
  intended prerequisite for every mapping pass.

These are project motivations. Detailed runtime behavior and failure rules belong
in the architecture; [next milestones](FEATURE_STATUS.md#suggested-next-sequence)
belong in the feature checklist rather than another roadmap here.

## Prototype success criteria

Demonstrate repeatable local mapping and navigation, reliable manual control and
stopping, and a task that finds a known object by querying remembered sightings,
visiting a valid observation position and confirming a fresh sighting. Richer
object descriptions should improve task choices without delaying ordinary
navigation. Success requires measured operation on real rover data, not only
architecture diagrams or sample-image inference.

## Future large rover scope

The eventual vehicle needs stronger motors, a suitable battery, steering,
hauling/towing hardware and independent safety systems. A 24 V utility platform,
garden-trolley donor chassis, geared wheelchair motors and actuator steering
remain options, not purchased or finalized requirements. Select drivetrain,
regulation and braking from measured load, current, terrain and stopping needs.

Hauling/trailer work is the first useful attachment scope. Powered implements
require separate power interlocks and substantial vehicle validation. The model
must not own propulsion isolation or implement safety. Larger-vehicle terrain
and obstacle sensing must be evaluated separately from the indoor 2D prototype.

The [4 October handoff](../archive/ROVER_HANDOFF_2026-10-04.md) retains the original
component ideas, indicative dimensions/budget and donor-chassis discussion.
It is historical rationale, not the current bill of materials or installation plan.
