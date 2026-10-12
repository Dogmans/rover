#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source "${ROVER_CAMERA_SETUP:-/home/barry/camera_ws/install/setup.bash}"
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:${LD_LIBRARY_PATH:-}
export PYTHONPATH=/opt/rover:${PYTHONPATH:-}
exec /usr/bin/python3 -m rover_hardware run camera
