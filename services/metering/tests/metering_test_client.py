import grpc
from services.metering.metering_pb2_grpc import MeteringStub
from services.metering.metering_pb2 import (
    MeterName, StatusRequest
)

if __name__ == '__main__':
    channel = grpc.insecure_channel('localhost:50051')
    client = MeteringStub(channel)
    meter_name = MeterName(name="i1Pro2_0")
    print('made MeterName', flush=True)
    request = StatusRequest(meter_name=meter_name)
    print('created StatusRequest', flush=True)
    client.ReportStatus(request)
