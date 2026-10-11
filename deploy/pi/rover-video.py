#!/usr/bin/python3
"""Encode local ROS camera frames into a low-delay H.264 TCP stream."""
import subprocess
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class Video(Node):
    def __init__(self):
        super().__init__('rover_video')
        self.encoder = None
        self.subscription = self.create_subscription(Image, '/camera/image_raw', self.frame,
                                                     qos_profile_sensor_data)

    def frame(self, msg):
        formats = {'rgb8': 'rgb24', 'bgr8': 'bgr24'}
        if msg.encoding not in formats or msg.step != msg.width * 3:
            raise ValueError(f'Unsupported camera layout: {msg.encoding}, step={msg.step}')
        if self.encoder is None:
            self.encoder = subprocess.Popen([
                'ffmpeg', '-hide_banner', '-loglevel', 'warning',
                '-f', 'rawvideo', '-pixel_format', formats[msg.encoding],
                '-video_size', f'{msg.width}x{msg.height}', '-framerate', '30', '-i', 'pipe:0',
                '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
                '-pix_fmt', 'yuv420p', '-r', '20', '-b:v', '2M', '-maxrate', '3M',
                '-bufsize', '500k', '-g', '20', '-bf', '0',
                '-x264-params', 'repeat-headers=1:aud=1:scenecut=0',
                '-f', 'mpegts', '-mpegts_flags', '+resend_headers', '-flush_packets', '1',
                '-muxdelay', '0', '-muxpreload', '0',
                'tcp://127.0.0.1:8554?listen=1'], stdin=subprocess.PIPE, bufsize=0)
            self.get_logger().info('H.264 MPEG-TS stream listening on TCP 8554')
        data = memoryview(msg.data)
        while data:
            written = self.encoder.stdin.write(data)
            if not written:
                raise BrokenPipeError('Video encoder stopped consuming frames')
            data = data[written:]

    def close(self):
        if self.encoder is not None:
            self.encoder.terminate()
            try:
                self.encoder.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.encoder.kill()
                self.encoder.wait()


def main():
    rclpy.init()
    node = Video()
    try:
        rclpy.spin(node)
    finally:
        node.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
