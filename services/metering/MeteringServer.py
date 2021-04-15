# -*- coding: utf-8 -*-
"""
A meter-access-and-control service using Google protobufs and gRPC
===================

Implements the functions required of a Metering server.

"""

from concurrent import futures
import grpc
from eieio.meter.xrite.i1pro import I1Pro
from services.metering.metering_pb2 import (
    StatusResponse, MeterDescription, IntegrationMode
)
import services.metering.metering_pb2_grpc as m_grpc


class MeteringService(m_grpc.MeteringServicer):
    # TODO
    def hotwire(self):
        self.meters['i1Pro2_0'] = I1Pro()

    def __init__(self):
        self.meters = {}
        self.hotwire()  # temporary

    def meter_description(self, name):
        if name not in self.meters.keys():
            return None
        meter = self.meters[name]
        print("in MeteringService's meter_description method", flush=True)
        return MeterDescription(make=meter.make(), model=meter.model(),
                                serial_number=meter.serial_number(),
                                firmware_version=meter.firmware_version(),
                                sdk_version=meter.sdk_version(),
                                adapter_version=meter.adapter_version(),
                                adapter_module_version=meter.adapter_module_version(),
                                integrationModes=[IntegrationMode.ADAPTIVE])

    def ReportStatus(self, request, context):
        meter_name = request.meter_name
        print(f"in MeteringService's ReportStatus method, meter_name is `{meter_name}"'', flush=True)
        description = self.meter_description(meter_name)
        if description:
            return StatusResponse(description=description)
        context.abort(grpc.StatusCode.NOT_FOUND, f"No meter named `{meter_name}' found")


class MeteringServer(object):
    def __init__(self):
        pass

    @staticmethod
    def serve():
        metering_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        m_grpc.add_MeteringServicer_to_server(MeteringService(), metering_server)
        metering_server.add_insecure_port('[::]:50051')
        metering_server.start()
        metering_server.wait_for_termination()


if __name__ == '__main__':
    print('Running metering server...', flush=True)
    MeteringServer.serve()
