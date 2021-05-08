from concurrent import futures
import threading
from signal import signal, SIGINT

import grpc
from targetColorChanging_pb2 import ChangeTargetColorResponse
from targetColorChanging_pb2_grpc import TargetColorChangingServicer, add_TargetColorChangingServicer_to_server

import nuke

COLOR_KNOB_NAME = 'color'

def set_node_color(request):
    node = nuke.toNode(request.node_name)
    if not node:
        return ChangeTargetColorResponse(changedOK=False, details=f"node `{request.node_name}' not found")
    knobs = node.knobs()
    if COLOR_KNOB_NAME not in knobs:
        return ChangeTargetColorResponse(changedOK=False, details=f"node `{request.node_name}' has no `color' knob")
    color_knob = knobs[COLOR_KNOB_NAME]
    new_value = [request.red, request.green, request.blue, 1.0]
    color_knob.setValue(new_value)
    if color_knob.value() == new_value:
        return ChangeTargetColorResponse(changedOK=True, details='color was set, and value read back matched')
    else:
        return ChangeTargetColorResponse(changedOK=False, details=f"node `{request.node_name}' failed to change color")


class TargetColorChangingService(TargetColorChangingServicer):
    def __init__(self):
        pass
    
    def ChangeTargetColor(self, request, context):
        return nuke.executeInMainThreadWithResult(set_node_color, request)


class ChangeTargetColorServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.grpc_server = None
        self.targetColorChangingService = None

    # def shutdown_service(self):
    #     self.targetColorChangingService = TargetColorChangingService()
    #     all_rpcs_done_event = self.grpc_server.stop(30)
    #     all_rpcs_done_event.wait(30)
    
    def serve(self):
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.targetColorChangingService = TargetColorChangingService()
        add_TargetColorChangingServicer_to_server(self.targetColorChangingService, self.grpc_server)
        self.grpc_server.add_insecure_port('[::]:50051')
        self.grpc_server.start()
        # signal(SIGINT, lambda signum, _: self.shutdown_service())
        self.grpc_server.wait_for_termination()

    def run(self):
        grpc_server = ChangeTargetColorServer()
        grpc_server.serve()


if __name__ == '__main__':
    server = ChangeTargetColorServer()
    server.start()
