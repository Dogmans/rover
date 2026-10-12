"""Hardware-boundary checks that run without ROS, a serial device or a Pi."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rover_hardware.contracts import CAMERA_IMAGE_TOPIC, LIDAR_FRAME, LIDAR_SCAN_TOPIC
from rover_hardware.drivers import parameter_arguments
from rover_hardware.profile import device_command, load_profile

PI_DIR = Path(__file__).resolve().parent
PROFILE = PI_DIR.parents[1] / 'config' / 'hardware' / 'ugv02-pi5.json'


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(PROFILE)

    def load_modified(self, profile):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hardware.json'
            path.write_text(json.dumps(profile), encoding='utf-8')
            return load_profile(path)

    def test_camera_preserves_commissioned_settings_and_contract(self):
        command = device_command(self.profile, 'camera')
        self.assertEqual(command[:4], ['ros2', 'run', 'camera_ros', 'camera_node'])
        parameters = dict(argument.split(':=', 1) for index, argument in enumerate(command)
                          if index > 0 and command[index - 1] == '-p')
        self.assertEqual({key: json.loads(value) for key, value in parameters.items()},
                         {'camera': 0, 'role': 'video', 'format': 'BGR888',
                          'width': 1280, 'height': 720})
        self.assertIn(f'/camera/image_raw:={CAMERA_IMAGE_TOPIC}', command)

    def test_camera_resolution_changes_only_the_profile(self):
        self.profile['devices']['camera']['driver_config']['parameters']['width'] = 640
        command = device_command(self.load_modified(self.profile), 'camera')
        self.assertIn('width:=640', command)
        self.assertIn(f'/camera/image_raw:={CAMERA_IMAGE_TOPIC}', command)

    def test_disabled_devices_cannot_start(self):
        for role in ('lidar', 'base'):
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'disabled'):
                device_command(self.profile, role)

    def test_uncommissioned_lidar_cannot_be_enabled(self):
        self.profile['devices']['lidar']['enabled'] = True
        with self.assertRaisesRegex(ValueError, 'verified package'):
            self.load_modified(self.profile)

    def test_two_sensor_drivers_keep_the_same_scan_and_frame_contract(self):
        # Deliberately fictional packages: this tests the adapter boundary,
        # not compatibility with a vendor's LD06 driver or physical sensor.
        for package, executable, topic, frame_parameter in (
                ('test_sensor_a', 'driver_a', '/sensor_a/scan', 'frame_id'),
                ('test_sensor_b', 'driver_b', '/measurements', 'scan_frame')):
            with self.subTest(package=package):
                profile = copy.deepcopy(self.profile)
                profile['devices']['lidar'].update(enabled=True, driver_config={
                    'package': package, 'executable': executable, 'scan_topic': topic,
                    'frame_parameter': frame_parameter,
                    'parameters': {'port': '/dev/serial/by-id/example', 'baud': 230400}})
                command = device_command(self.load_modified(profile), 'lidar')
                self.assertEqual(command[:4], ['ros2', 'run', package, executable])
                self.assertIn(f'{topic}:={LIDAR_SCAN_TOPIC}', command)
                self.assertIn(f'{frame_parameter}:="{LIDAR_FRAME}"', command)

    def test_conflicting_lidar_frame_is_rejected(self):
        self.profile['devices']['lidar'].update(enabled=True, driver_config={
            'package': 'test_sensor', 'executable': 'test_driver', 'scan_topic': '/raw_scan',
            'frame_parameter': 'frame_id', 'parameters': {'frame_id': 'wrong_frame'}})
        with self.assertRaisesRegex(ValueError, 'must publish in lidar_link'):
            self.load_modified(self.profile)

    def test_unknown_driver_and_wrong_role_are_rejected(self):
        for driver in ('missing_driver', 'ros_laserscan'):
            with self.subTest(driver=driver):
                profile = copy.deepcopy(self.profile)
                profile['devices']['camera']['driver'] = driver
                with self.assertRaises(ValueError):
                    self.load_modified(profile)

    def test_invalid_profile_and_camera_parameters_are_rejected(self):
        for change in ('schema', 'enabled', 'dimensions', 'missing_role', 'parameter_type'):
            with self.subTest(change=change):
                profile = copy.deepcopy(self.profile)
                if change == 'schema':
                    profile['schema_version'] = True
                elif change == 'enabled':
                    profile['devices']['lidar']['enabled'] = 'false'
                elif change == 'dimensions':
                    profile['devices']['camera']['driver_config']['parameters']['width'] = -1
                elif change == 'missing_role':
                    del profile['devices']['base']
                else:
                    profile['devices']['camera']['driver_config']['parameters']['format'] = []
                with self.assertRaises(ValueError):
                    self.load_modified(profile)

    def test_parameters_preserve_types_and_remain_separate_arguments(self):
        value = '/dev/example; $(echo should-not-run)'
        command = parameter_arguments({'port': value, 'label': 'true', 'enabled': False})
        self.assertEqual(json.loads(command[1].split(':=', 1)[1]), value)
        self.assertEqual(json.loads(command[3].split(':=', 1)[1]), 'true')
        self.assertIs(json.loads(command[5].split(':=', 1)[1]), False)

    def test_invalid_parameter_values_are_rejected(self):
        for value in (None, [], {}, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parameter_arguments({'value': value})

    def test_cli_checks_profile_and_refuses_disabled_driver_without_ros(self):
        env = dict(os.environ, PYTHONPATH=str(PI_DIR))
        for arguments, status in ((['check'], 0), (['command', 'camera'], 0),
                                  (['run', 'lidar'], 2)):
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, '-m', 'rover_hardware',
                                         '--profile', str(PROFILE), *arguments],
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
