#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export PYTHONPATH=/opt/rover:${PYTHONPATH:-}
exec /usr/bin/python3 /usr/local/bin/rover-video.py
