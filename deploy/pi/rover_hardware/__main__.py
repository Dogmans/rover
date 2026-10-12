"""Inspect, validate or run one configured hardware adapter."""
import argparse
import os
import shlex
import sys

from .profile import device_command, load_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default=os.environ.get(
        'ROVER_HARDWARE_PROFILE', '/etc/rover/hardware.json'))
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('check', help='validate all enabled devices without starting ROS')
    commands.add_parser('describe', help='show inventory and commissioning status')
    for action in ('command', 'run'):
        child = commands.add_parser(action)
        child.add_argument('role', choices=('camera', 'lidar', 'base'))
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile)
        if args.action == 'check':
            print(f'Valid hardware profile: {profile["profile"]}')
        elif args.action == 'describe':
            print(f'{profile["profile"]}: {profile["host"].get("model", "unspecified host")}')
            for role, device in profile['devices'].items():
                state = 'enabled' if device['enabled'] else 'disabled'
                print(f'{role}: {device["model"]} ({state}, driver={device["driver"]})')
                print(f'  {device["connection"]}; {device["status"]}')
        else:
            command = device_command(profile, args.role)
            if args.action == 'command':
                print(shlex.join(command))
            else:
                os.execvp(command[0], command)
    except (OSError, ValueError) as exc:
        print(f'Hardware configuration error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
