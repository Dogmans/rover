"""Adapter for the commissioned CSI camera_ros node."""
from ..contracts import CAMERA_IMAGE_TOPIC, CAMERA_INFO_TOPIC
from . import parameter_arguments


def command(config):
    parameters = config.get('parameters')
    if not isinstance(parameters, dict):
        raise ValueError('camera_ros requires parameters')
    for name in ('camera', 'width', 'height'):
        value = parameters.get(name)
        minimum = 0 if name == 'camera' else 1
        if type(value) is not int or value < minimum:
            raise ValueError(f'camera_ros {name} must be an integer >= {minimum}')
    for name in ('role', 'format'):
        if not isinstance(parameters.get(name), str) or not parameters[name]:
            raise ValueError(f'camera_ros requires {name}')
    return ['ros2', 'run', 'camera_ros', 'camera_node', '--ros-args',
            *parameter_arguments(parameters),
            '-r', f'/camera/image_raw:={CAMERA_IMAGE_TOPIC}',
            '-r', f'/camera/camera_info:={CAMERA_INFO_TOPIC}']
