"""Explicit adapter registry: profiles cannot execute arbitrary Python imports."""
import json
import math
import re


def parameter_arguments(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('driver parameters must be an object')
    arguments = []
    for name, value in parameters.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', name):
            raise ValueError(f'invalid ROS parameter name: {name}')
        if type(value) not in (str, int, float, bool):
            raise ValueError(f'parameter {name} must be a string, number or boolean')
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f'parameter {name} must be finite')
        # JSON scalars are valid YAML scalars. Quote strings to preserve types,
        # including serial paths and values such as "true" or "123".
        arguments.extend(['-p', f'{name}:={json.dumps(value)}'])
    return arguments


def command_for(role, device):
    from . import camera_ros, ros_laserscan

    adapters = {'camera_ros': ('camera', camera_ros),
                'ros_laserscan': ('lidar', ros_laserscan)}
    driver = device['driver']
    if driver not in adapters:
        raise ValueError(f'{role}: driver {driver!r} is not implemented')
    expected_role, adapter = adapters[driver]
    if role != expected_role:
        raise ValueError(f'{driver} cannot provide the {role} interface')
    return adapter.command(device['driver_config'])
