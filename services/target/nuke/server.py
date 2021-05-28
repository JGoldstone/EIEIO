from concurrent import futures
import os
import threading
import time

import grpc
from target_pb2 import ChangeTargetColorResponse
from target_pb2_grpc import TargetColorChangingServicer, add_TargetColorChangingServicer_to_server

import nuke

PORT_TARGET_COLOR_CHANGING = 51002
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
COLOR_KNOB_NAME = 'color'


class ColorChanger(TargetColorChangingServicer):
    def __init__(self, mocking=False):
        self._mocking = mocking
        self.mocking = mocking
        print(f"creating ColorChanger (mocking is {self.mocking})")

    @property
    def mocking(self):
        return self._mocking

    @mocking.setter
    def mocking(self, value):
        self._mocking = value

    def set_node_color(self, request):
        patch_name = request.patch_name
        red = request.red
        green = request.green
        blue = request.blue
        if self.mocking:
            print(f"saw request to change color of {patch_name} to ({red}, {green}, {blue}", flush=True)
            fail_requested = patch_name.starts_with('fail_')
            return ChangeTargetColorResponse(changedOK=False if fail_requested else True,
                                             details='fail requested' if fail_requested else None)
        node = nuke.toNode(patch_name)
        if not node:
            return ChangeTargetColorResponse(changedOK=False, details=f"node `{request.patch_name}' not found")
        knobs = node.knobs()
        if COLOR_KNOB_NAME not in knobs:
            return ChangeTargetColorResponse(changedOK=False,
                                             details=f"node `{request.patch_name}' has no `color' knob")
        color_knob = knobs[COLOR_KNOB_NAME]
        new_value = [request.red, request.green, request.blue, 1.0]
        color_knob.setValue(new_value)
        if color_knob.value() == new_value:
            return ChangeTargetColorResponse(changedOK=True, details='color was set, and value read back matched')
        else:
            return ChangeTargetColorResponse(changedOK=False,
                                             details=f"node `{request.patch_name}' failed to change color")

    def ChangeTargetColor(self, request, context):
        os.environ["NUKE_INTERACTIVE"] = "1"
        print("about to execute self.set_node_color on main thread", flush=True)
        return nuke.executeInMainThreadWithResult(self.set_node_color, request)


class Daemon(threading.Thread):
    def __init__(self, daemon=True, mocking=False):
        threading.Thread.__init__(self, daemon=daemon)
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self._mocking = False
        self.mocking = mocking
        self.color_changer = ColorChanger(mocking=self.mocking)
        print('target daemon instance created', flush=True)

    @property
    def mocking(self):
        return self._mocking

    @mocking.setter
    def mocking(self, value):
        self._mocking = value
    
    def serve(self):
        add_TargetColorChangingServicer_to_server(self.color_changer, self.grpc_server)
        self.grpc_server.add_insecure_port(f"[::]:{PORT_TARGET_COLOR_CHANGING}")
        self.grpc_server.start()
        print('grpc server started', flush=True)
        if self.mocking:
            try:
                while True:
                    print('about to sleep for a day', flush=True)
                    time.sleep(_ONE_DAY_IN_SECONDS)
            except KeyboardInterrupt:
                self.grpc_server.stop(0)

    def run(self):
        self.serve()

# How to use from a Nuke script editor
# from eieio.services.target.nuke import Daemon
# d = Daemon()
# d.start()


if __name__ == '__main__':
    _daemon = Daemon(daemon=False, mocking=True)
    _daemon.start()  # which will call the Daemon's run() method and we're off to the races
