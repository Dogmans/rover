#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source /home/barry/camera_ws/install/setup.bash
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:${LD_LIBRARY_PATH:-}
exec ros2 run camera_ros camera_node --ros-args \
  -p camera:=0 -p role:=video -p format:=BGR888 \
  -p width:=1280 -p height:=720
