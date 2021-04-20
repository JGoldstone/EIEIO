# -*- coding: utf-8 -*-
"""
A meter_desc-access-and-control service using Google protobufs and gRPC
===================

Implements the functions required of a Metering server.

"""

from datetime import datetime, timedelta
from concurrent import futures
import grpc

from eieio.meter.xrite.i1pro import I1Pro
# from services.metering.metering_pb2 import (
#     StringStatusResponse,
#     MeterName,
#     MeterNameStatusResponse,
#     WrappedMeterName,
#     WrappedMeterNameStatusResponse,
#     StatusResponse, MeterDescription, IntegrationMode
# )

from metering_pb2 import MeterName, MeterDescription, StatusResponse, CalibrationResponse
from metering_pb2_grpc import MeteringServicer, add_MeteringServicer_to_server


class MeteringService(MeteringServicer):
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
        # This set of intermediaries is here to make it easier to determine which meter method failed
        make = meter.make()
        model = meter.model()
        serial_number = meter.serial_number()
        firmware_version = meter.firmware_version()
        sdk_version = meter.sdk_version()
        adapter_version = meter.adapter_version()
        adapter_module_version = meter.adapter_module_version()
        supported_measurement_modes = meter.measurement_modes()
        current_measurement_mode = meter.measurement_mode()
        supported_integration_modes = meter.integration_modes()
        current_integration_mode = meter.integration_mode()
        supported_measurement_angles = meter.measurement_angles()
        current_measurement_angle = meter.measurement_angle()
        return MeterDescription(name=MeterName(name=name),
                                make=make, model=model,
                                serial_number=serial_number,
                                firmware_version=firmware_version,
                                sdk_version=sdk_version,
                                adapter_version=adapter_version,
                                adapter_module_version=adapter_module_version,
                                supported_measurement_modes=supported_measurement_modes,
                                current_measurement_mode=current_measurement_mode,
                                supported_integration_modes=supported_integration_modes,
                                current_integration_mode=current_integration_mode,
                                supported_measurement_angles=supported_measurement_angles,
                                current_measurement_angle=current_measurement_angle)

    def ReportStatus(self, request, context):
        meter_name = request.meter_name.name
        description = self.meter_description(meter_name)
        if description:
            return StatusResponse(description=description)
        context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")

    def Calibrate(self, request, context):
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        if request.mode:
            measurement_modes = [meter.mode]
        else:
            measurement_modes = meter.measurement_modes()
        needs_recalibrating = False
        for measurement_mode in measurement_modes:
            meter.set_measurement_mode(measurement_mode)
            since, until = meter.calibration_times()
            remaining = until - datetime.now()
            short_session_time = timedelta(minutes=10)
            if remaining < short_session_time:  # do we have ten minutes to make a measurement?
                needs_recalibrating = True
        if not needs_recalibrating:
            return CalibrationResponse()
        meter.promptForCalibrationPositioning()
        for measurement_mode in measurement_modes:
            meter.set_measurement_mode(measurement_mode)
            meter.calibrate()
        meter.promptForMeasurementPositioning()
        return CalibrationResponse()


class MeteringServer(object):
    def __init__(self):
        pass

    @staticmethod
    def serve():
        metering_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_MeteringServicer_to_server(MeteringService(), metering_server)
        metering_server.add_insecure_port('[::]:50051')
        metering_server.start()
        metering_server.wait_for_termination()


if __name__ == '__main__':
    print('Running metering server...', flush=True)
    MeteringServer.serve()
