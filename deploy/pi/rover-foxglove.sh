#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
exec ros2 launch foxglove_bridge foxglove_bridge_launch.xml \
  port:=8765 address:=0.0.0.0
