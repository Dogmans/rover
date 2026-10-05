# External references for Pi 5 / ROS 2 / UGV02 setup

These are the primary vendor and platform references used to shape the configuration plan.

## Waveshare

- UGV02 product documentation: https://www.waveshare.com/wiki/UGV02
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
- ROS 2 Navigation (Nav2): https://github.com/ros-navigation/navigation2

The rover-specific assessment and recommendation are recorded in [ACTION_MODEL_RESEARCH.md](ACTION_MODEL_RESEARCH.md). Model availability, checkpoints, hardware requirements, and licenses can change; recheck upstream documentation before selecting or deploying a model.

## Notes from the official references

- Waveshare UGV02 exposes UART/JSON control to the host computer, and the host communicates with the ESP32 over GPIO UART at 115200 baud.
- The ROS Driver board is not the same as a ROS-native controller; a host-side ROS driver or adapter is required.
- The host-side UGV Pi repo includes installation and autorun scripts for the Raspberry Pi side.
- Raspberry Pi OS Bookworm uses the modern libcamera/rpicam stack; the legacy raspistill stack is deprecated and should not be the target path.
- The Pi camera module is an official CSI camera and must be used via the modern Raspberry Pi camera stack.
