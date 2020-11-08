import argparse
import time
from threading import Lock
import MDAnalysis as mda
from narupa.mdanalysis import mdanalysis_to_frame_data
from narupa.app import NarupaFrameApplication
from narupa.trajectory.frame_server import (
    PLAY_COMMAND_KEY, PAUSE_COMMAND_KEY, RESET_COMMAND_KEY, STEP_COMMAND_KEY,
)
from narupa.utilities.timing import yield_interval


class TrajectoryRunner:
    def __init__(self, topology, trajectory):
        self._app = NarupaFrameApplication.basic_server()

        self._universe_lock = Lock()
        self._universe = mda.Universe(topology, trajectory)

        self._seek_lock = Lock()
        self._seek_target = None
        self._paused_lock = Lock()
        self._paused = False
        self._framerate_lock = Lock()
        self._sending_frames_per_seconds = 30

        self._register_commands()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._app.close()

    def _register_commands(self):
        self._app.server.register_command(PLAY_COMMAND_KEY, self.play)
        self._app.server.register_command(PAUSE_COMMAND_KEY, self.pause)
        self._app.server.register_command(RESET_COMMAND_KEY, self.reset)
        self._app.server.register_command(STEP_COMMAND_KEY, self.step_forward)
        self._app.server.register_command('trajectory/step-backward', self.step_backward)
        self._app.server.register_command('trajectory/seek', self.seek)
        self._app.server.register_command('trajectory/set-framerate', self.set_framerate)


    def _change_to_frame(self, frame_index):
        with self._universe_lock:
            self._universe.trajectory[frame_index]
    
    def _send_frame(self, frame_index, topology=False):
        self._change_to_frame(frame_index)
        with self._universe_lock:
            frame = mdanalysis_to_frame_data(self._universe, topology=topology)
        if topology:
            frame.values.set('trajectory.frame.count', self.n_frames)
        frame.values.set('trajectory.frame', frame_index)
        self._app.frame_publisher.send_frame(frame_index, frame)

    @property
    def n_frames(self):
        return self._universe.trajectory.n_frames
    
    @property
    def sending_frames_per_seconds(self):
        return self._sending_frames_per_seconds
    
    @sending_frames_per_seconds.setter
    def sending_frames_per_seconds(self, framerate):
        with self._framerate_lock:
            self._sending_frames_per_seconds = framerate

    @property
    def send_interval(self):
        return 1 / self.sending_frames_per_seconds

    def _yield_interval(self):
        """
        Yield at a set interval, accounting for the time spent outside of this
        function.

        :param interval: Number of seconds to put between yields
        """
        last_yield = time.monotonic() - self.send_interval
        while True:
            time_since_yield = time.monotonic() - last_yield
            wait_duration = max(0., self.send_interval - time_since_yield)
            time.sleep(wait_duration)
            yield time.monotonic() - last_yield
            last_yield = time.monotonic()    

    def run(self):
        frame_index = 0
        self._send_frame(0, topology=True)
        for _ in self._yield_interval():
            with self._seek_lock:
                if self._seek_target is not None:
                    frame_index = self._seek_target
                    self._seek_target = None
                    self._send_frame(frame_index)
                    self.pause()
            if not self._paused:
                frame_index += 1
                if frame_index >= self.n_frames:
                    frame_index = 0
                self._send_frame(frame_index)
            else:
                time.sleep(1/30)

    def play(self):
        with self._paused_lock:
            self._paused = False

    def pause(self):
        with self._paused_lock:
            self._paused = True
    
    def reset(self):
        self.seek(0)

    def seek(self, frame_index):
        frame_index = int(frame_index)
        if frame_index >= self.n_frames:
            raise IndexError
        with self._seek_lock:
            self._seek_target = frame_index
    
    def step_offset(self, offset):
        with self._universe_lock:
            frame_index = self._universe.trajectory.frame
        target = frame_index + offset
        self.seek(target)
    
    def step_forward(self):
        self.step_offset(1)
    
    def step_backward(self):
        self.step_offset(-1)
    
    def set_framerate(self, framerate):
        self.sending_frames_per_seconds = framerate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topology")
    parser.add_argument("trajectory")
    args = parser.parse_args()

    with TrajectoryRunner(args.topology, args.trajectory) as runner:
        print('Ready to go!')
        runner.run()

if __name__ == "__main__":
    main()
