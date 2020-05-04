#!/usr/bin/env python

import argparse
import sys
import time

from narupa.ase.openmm.runner import OpenMMIMDRunner, ImdParams, LoggingParams
from narupa.openmm.serializer import deserialize_simulation
from narupa.trajectory.frame_server import PAUSE_COMMAND_KEY, PLAY_COMMAND_KEY

NARUPA_PORT = 38801
DEFAULT_WALLTIME = 30  # minutes
DEFAULT_CONNECTION_DELAY = 5  # minutes
DEFAULT_TIMEOUT = 2  # minues


class CloudRunner:
    def __init__(self, simulation_path, walltime, connection_delay, timeout):
        with open(args.simulation_path) as infile:
            self.simulation = deserialize_simulation(infile.read())

        self.connection_delay = connection_delay * 60  # in seconds
        self.timeout = timeout * 60  # in seconds
        self.walltime = walltime * 60  # in seconds
        self.time_last_seen_avatar = None
        self.enf_time = None

        self.imd_params = ImdParams(port=NARUPA_PORT, verbose=True)
        self._running = False
        self._runner = OpenMMIMDRunner(self.simulation, self.imd_params)
        self._register_commands()
    
    def _register_commands(self):
        self._runner.imd._server.unregister_command(PAUSE_COMMAND_KEY)
        self._runner.imd._server.register_command(PAUSE_COMMAND_KEY, self._pause)
        self._runner.imd._server.unregister_command(PLAY_COMMAND_KEY)
        self._runner.imd._server.register_command(PLAY_COMMAND_KEY, self._play)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._runner.close()

    def _pause(self):
        self._running = False
    
    def _play(self):
        self._running = True
    
    def _get_avatars(self):
        return self._runner.app_server._multiplayer._avatars.copy_content()

    def has_active_avatar(self):
        return any(avatar.components for avatar in self._get_avatars().values())
    
    def get_timeout_checker(self):
        starting_time = time.monotonic()
        end_connection_delay = starting_time + self.connection_delay
        end_timeout = starting_time + self.timeout
        end_walltime = starting_time + self.walltime
        while True:
            now = time.monotonic()
            if self.has_active_avatar():
                end_timeout = now + self.timeout
            passed_walltime = now > end_walltime
            passed_timeout = now > end_connection_delay and now > end_timeout
            yield passed_walltime or passed_timeout
    
    def run(self):
        self.end_time = time.monotonic() + self.walltime
        self._running = True
        
        timeout_cheker = self.get_timeout_checker()
        while not next(timeout_cheker):
            if self._running:
                self._runner.run(5)
            else:
                time.sleep(0.3)
        self._running = False


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('simulation_path')
    arg_parser.add_argument(
        '--walltime', type=float, default=DEFAULT_WALLTIME,
        help='Maximum duration of a session, in minutes.',
    )
    arg_parser.add_argument(
        '--connection-delay', type=float, default=DEFAULT_CONNECTION_DELAY,
        help='Duration alowed for the first avatar to connect, in minutes.'
    )
    arg_parser.add_argument(
        '--timeout', type=float, default=DEFAULT_TIMEOUT,
        help='Duration between the last avatar is seen and the session end, '
             'in minutes.',
    )
    args = arg_parser.parse_args()

    runner = CloudRunner(
        args.simulation_path,
        walltime=args.walltime,
        connection_delay=args.connection_delay,
        timeout=args.timeout,
    )
    with runner:
        runner.run()