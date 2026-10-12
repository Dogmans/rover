"""Load a versioned hardware profile without requiring ROS or third-party libs."""
import json
from pathlib import Path

from .drivers import command_for


def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding='utf-8'))
    if (not isinstance(profile, dict)
            or type(profile.get('schema_version')) is not int
            or profile['schema_version'] != 1):
        raise ValueError('hardware profile requires schema_version 1')
    if not isinstance(profile.get('profile'), str) or not profile['profile']:
        raise ValueError('hardware profile requires a profile name')
    if not isinstance(profile.get('host'), dict):
        raise ValueError('hardware profile requires host metadata')
    devices = profile.get('devices')
    if not isinstance(devices, dict) or set(devices) != {'camera', 'lidar', 'base'}:
        raise ValueError('hardware profile requires camera, lidar and base device roles')
    for role, device in devices.items():
        if not isinstance(device, dict):
            raise ValueError(f'{role} must be an object')
        for field in ('model', 'connection', 'status'):
            if not isinstance(device.get(field), str) or not device[field]:
                raise ValueError(f'{role} requires {field} metadata')
        if type(device.get('enabled')) is not bool:
            raise ValueError(f'{role}.enabled must be a boolean')
        if device.get('driver') is not None and not isinstance(device['driver'], str):
            raise ValueError(f'{role}.driver must be a string or null')
        if 'driver' not in device or not isinstance(device.get('driver_config'), dict):
            raise ValueError(f'{role} requires driver and driver_config')
        if device['enabled']:
            command_for(role, device)
    return profile


def device_command(profile, role):
    device = profile['devices'][role]
    if not device['enabled']:
        raise ValueError(f'{role} is disabled in profile {profile["profile"]}')
    return command_for(role, device)
