"""Wrap a ROS LaserScan driver; serial/protocol handling stays in that driver.

Use a dedicated adapter instead if a sensor needs conversion or a launch file.
No particular LD06 package or parameter names are assumed here.
"""
import re

from ..contracts import LIDAR_FRAME, LIDAR_SCAN_TOPIC
from . import parameter_arguments


def command(config):
    for name in ('package', 'executable'):
        value = config.get(name)
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]*', value):
            raise ValueError(f'ros_laserscan requires a verified {name}')
    source = config.get('scan_topic')
    if not isinstance(source, str) or not re.fullmatch(r'/(?:[A-Za-z_][A-Za-z0-9_]*/)*[A-Za-z_][A-Za-z0-9_]*', source):
        raise ValueError('ros_laserscan requires an absolute source scan_topic')
    frame_parameter = config.get('frame_parameter')
    if not isinstance(frame_parameter, str) or not frame_parameter:
        raise ValueError('ros_laserscan requires the verified frame_parameter name')
    parameters = config.get('parameters')
    if not isinstance(parameters, dict):
        raise ValueError('ros_laserscan requires parameters')
    parameters = dict(parameters)
    if frame_parameter in parameters and parameters[frame_parameter] != LIDAR_FRAME:
        raise ValueError(f'LiDAR must publish in {LIDAR_FRAME}')
    parameters[frame_parameter] = LIDAR_FRAME
    return ['ros2', 'run', config['package'], config['executable'], '--ros-args',
            *parameter_arguments(parameters), '-r', f'{source}:={LIDAR_SCAN_TOPIC}']
