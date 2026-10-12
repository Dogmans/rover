# External references for Pi 5 / ROS 2 / UGV02 setup

This is a source index, not a setup procedure or runtime specification. The
[architecture](../architecture/ROS_ARCHITECTURE.md) owns selected direction,
[hardware stack](../hardware/HARDWARE_STACK.md) owns parts, and
[model research](ACTION_MODEL_RESEARCH.md) owns candidate assessment. Upstream
content can change; dated evidence remains in the [archive](../archive/README.md).

## Waveshare

- UGV02 product documentation: https://www.waveshare.com/wiki/UGV02
- UGV02 IMU/encoder interface findings and source links: [base telemetry notes](../hardware/UGV02_BASE_TELEMETRY.md)
- UGV Rover PI ROS2 overview: https://www.waveshare.com/wiki/UGV_Rover_PI_ROS2
- Upper computer example repo: https://github.com/waveshareteam/ugv_rpi
- Lower computer ESP32 ROS driver repo: https://github.com/waveshareteam/ugv_base_ros
- Lower computer general driver repo: https://github.com/waveshareteam/ugv_base_general
- Driver board schematic: https://files.waveshare.com/wiki/RaspRover/ROS_Driver_for_Robots.pdf
- ESP32 flash tool: https://files.waveshare.com/wiki/UGV02/UGV02_FACTORY_250226.zip

## Raspberry Pi

- Getting started: https://www.raspberrypi.com/documentation/computers/getting-started.html
- Camera software: https://www.raspberrypi.com/documentation/computers/camera_software.html
- Raspberry Pi OS documentation: https://www.raspberrypi.com/documentation/computers/os.html
- Raspberry Pi Imager: https://www.raspberrypi.com/software/

## Foxglove

- Foxglove Bridge overview and remote access: https://docs.foxglove.dev/docs/fleet/bridge
- ROS 2 getting started: https://docs.foxglove.dev/docs/getting-started/frameworks/ros2

## Action models and local vision-language models

- Qwen3-VL model family and inference: https://github.com/QwenLM/Qwen3-VL
- Cloudflare Clef and Clef-Flash announcement: https://blog.cloudflare.com/clef-decision-models/
- Cloudflare Clef model card: https://huggingface.co/Cloudflare/clef
- Cloudflare Clef-Flash model card: https://huggingface.co/Cloudflare/clef-flash
- Cloudflare Workers AI Clef deployment docs: https://developers.cloudflare.com/workers-ai/models/clef/
- TypeSafe / Jev model documentation: https://docs.typesafe.ai/models
- TypeSafe System One concepts: https://docs.typesafe.ai/concepts/system-one
- Hugging Face LeRobot VLA-JEPA documentation: https://huggingface.co/docs/lerobot/main/vla_jepa
- Hugging Face LeRobot SmolVLA documentation: https://huggingface.co/docs/lerobot/main/smolvla
- OpenVLA research implementation: https://github.com/openvla/openvla
- Physical Intelligence open π models: https://github.com/Physical-Intelligence/openpi
- Meta V-JEPA 2 research and checkpoints: https://github.com/facebookresearch/vjepa2
- LeRobot robotics models, datasets, and policy framework: https://github.com/huggingface/lerobot

The rover-specific assessment and recommendation are recorded in [ACTION_MODEL_RESEARCH.md](ACTION_MODEL_RESEARCH.md). Model availability, checkpoints, hardware requirements, and licenses can change; recheck upstream documentation before selecting or deploying a model.

## Navigation and transport

- ROS 2 Navigation (Nav2): https://github.com/ros-navigation/navigation2
- SLAM Toolbox: https://github.com/SteveMacenski/slam_toolbox
- State-estimation/fusion package: https://github.com/cra-ros-pkg/robot_localization
- Windows-compatible ROS transport candidate: https://github.com/RobotWebTools/rosbridge_suite/tree/ros2
- ROS message definitions: https://github.com/ros2/common_interfaces/tree/jazzy

Package presence in this index does not imply installation or rover validation.
Firmware behavior and sensor conversion findings are recorded in
[UGV02 base telemetry](../hardware/UGV02_BASE_TELEMETRY.md), not duplicated here.
