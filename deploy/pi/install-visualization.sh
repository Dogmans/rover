#!/usr/bin/env bash
# Run from this directory on the commissioned ROBOT Pi.
set -euo pipefail
cd -- "$(dirname -- "$0")"
test -f "${ROVER_CAMERA_SETUP:-/home/barry/camera_ws/install/setup.bash}"
profile_source="../../config/hardware/ugv02-pi5.json"
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python3 -m rover_hardware --profile "$profile_source" check
sudo -n install -d /opt/rover/rover_hardware/drivers /etc/rover
# Preserve site-specific device paths and settings on subsequent installs.
if ! sudo -n test -f /etc/rover/hardware.json; then
  sudo -n install -m 0644 "$profile_source" /etc/rover/hardware.json
fi
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python3 -m rover_hardware --profile /etc/rover/hardware.json check
sudo -n install -m 0644 rover_hardware/*.py /opt/rover/rover_hardware/
sudo -n install -m 0644 rover_hardware/drivers/*.py /opt/rover/rover_hardware/drivers/
sudo -n apt-get update
sudo -n apt-get install -y ffmpeg ros-jazzy-compressed-image-transport
sudo -n install -m 0755 rover-camera.sh /usr/local/bin/rover-camera
sudo -n install -m 0755 rover-lidar.sh /usr/local/bin/rover-lidar
sudo -n install -m 0755 rover-foxglove.sh /usr/local/bin/rover-foxglove
sudo -n install -m 0755 rover-video.sh /usr/local/bin/rover-video
sudo -n install -m 0755 rover-video.py /usr/local/bin/rover-video.py
sudo -n install -m 0644 rover-camera.service rover-foxglove.service /etc/systemd/system/
sudo -n install -m 0644 rover-video.service /etc/systemd/system/
sudo -n install -m 0644 rover-lidar.service /etc/systemd/system/
# LiDAR is installed but not enabled: the checked-in profile is uncommissioned.
sudo -n systemctl daemon-reload
sudo -n systemctl enable rover-camera.service rover-foxglove.service
sudo -n systemctl enable --now rover-video.service
sudo -n systemctl restart rover-camera.service rover-foxglove.service
systemctl --no-pager status rover-camera.service rover-foxglove.service
