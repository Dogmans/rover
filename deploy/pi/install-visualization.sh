#!/usr/bin/env bash
# Run from this directory on the commissioned ROBOT Pi.
set -euo pipefail
cd -- "$(dirname -- "$0")"
test -f /home/barry/camera_ws/install/setup.bash
sudo -n apt-get update
sudo -n apt-get install -y ffmpeg ros-jazzy-compressed-image-transport
sudo -n install -m 0755 rover-camera.sh /usr/local/bin/rover-camera
sudo -n install -m 0755 rover-foxglove.sh /usr/local/bin/rover-foxglove
sudo -n install -m 0755 rover-video.sh /usr/local/bin/rover-video
sudo -n install -m 0755 rover-video.py /usr/local/bin/rover-video.py
sudo -n install -m 0644 rover-camera.service rover-foxglove.service /etc/systemd/system/
sudo -n install -m 0644 rover-video.service /etc/systemd/system/
sudo -n systemctl daemon-reload
sudo -n systemctl enable rover-camera.service rover-foxglove.service
sudo -n systemctl enable --now rover-video.service
sudo -n systemctl restart rover-camera.service rover-foxglove.service
systemctl --no-pager status rover-camera.service rover-foxglove.service
