#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
if [[ -n "${ROVER_LIDAR_SETUP:-}" ]]; then
  source "$ROVER_LIDAR_SETUP"
fi
export PYTHONPATH=/opt/rover:${PYTHONPATH:-}
exec /usr/bin/python3 -m rover_hardware run lidar
