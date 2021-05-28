import grpc
import target_pb2_grpc
from target_pb2 import ChangeTargetColorRequest
from services.ports import PORT_TARGET_COLOR_CHANGING

# HOST = 'localhost'
HOST = '10.0.20.151'

if __name__ == '__main__':
    with grpc.insecure_channel(f"{HOST}:{PORT_TARGET_COLOR_CHANGING}", options=(('grpc.enmable_http_proxy', 0),)) as channel:
        client = target_pb2_grpc.TargetColorChangingStub(channel)
        request = ChangeTargetColorRequest(patch_name='Constant1', red=0.25, green=0.5, blue=1.0)
        response = client.ChangeTargetColor(request)
        color = f"({request.red}, {request.green}, {request.blue}, 1.0)"
        if response.changedOK:
            print(f"successfully changed color to {color}")
        else:
            print(f"failed to change color to {color}")
