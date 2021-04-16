import grpc
import metering_pb2
import metering_pb2_grpc
# from services.metering.metering_pb2 import (
#     MeterName, StringStatusRequest, MeterNameStatusRequest,
#     WrappedMeterNameStatusRequest, StatusRequest
# )

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        client = metering_pb2_grpc.MeteringStub(channel)

        string_status_request = metering_pb2.StringStatusRequest(meter_name="i1Pro2_0")
        print('made StringStatusRequest', flush=True)
        client.ReportStringStatus(string_status_request)
        print('back from ReportStringStatus', flush=True)

        meter_name_status_request = metering_pb2.MeterNameStatusRequest(meter_name="i1Pro2_0")
        print('made MeterNameStatusRequest', flush=True)
        response = client.ReportMeterNameStatus(meter_name_status_request)
        print('back from ReportMeterNameStatus', flush=True)
        print(f"meter name is `{response.meter_name.name}'", flush=True)

        wrapped_meter_name_status_request = metering_pb2.WrappedMeterNameStatusRequest(meter_name="i1Pro2_0")
        print('made WrappedMeterNameStatusRequest', flush=True)
        response = client.ReportWrappedMeterNameStatus(wrapped_meter_name_status_request)
        print('back from WrappedReportMeterNameStatus', flush=True)
        print(f"meter name is `{response.meter_name.meter_name.name}'", flush=True)

        meter_name = metering_pb2.MeterName(name="i1Pro2_0")
        print('made MeterName', flush=True)
        request = metering_pb2.StatusRequest(meter_name=meter_name)
        print('made StatusRequest', flush=True)
        response = client.ReportStatus(request)
        print('back from ReportStatus', flush=True)
        print(f"meter name is `{response.description.name.name}'", flush=True)
