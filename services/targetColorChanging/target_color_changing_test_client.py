# import grpc
# import targetColorChanging_pb2_grpc
# from targetColorChanging_pb2 import ChangeTargetColorRequest
# from services.port import PORT_METERING
#
# if __name__ == '__main__':
#     with grpc.insecure_channel(f"localhost:{PORT_METERING}") as channel:
#         client = targetColorChanging_pb2_grpc.TargetColorChangingStub(channel)
#         request = ChangeTargetColorRequest(node_name='Constant1', red=0.25, green=0.5, blue=1.0)
#         response = client.ChangeTargetColor(request)
#         color = f"({request.red}, {request.green}, {request.blue}, 1.0)"
#         if response.changedOK:
#             print(f"successfully changed color to {color}")
#         else:
#             print(f"failed to change color to {color}")
