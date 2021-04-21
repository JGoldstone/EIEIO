# -*- coding: utf-8 -*-
"""
A meter_desc-access-and-control service using Google protobufs and gRPC
===================

Implements the functions required of a Metering server.

"""

from datetime import datetime, timedelta
from concurrent import futures
import numpy as np

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

from metering_pb2 import (GenericErrorCode,
                          MeterName, MeterDescription,
                          StatusResponse,
                          CalibrationError, CalibrationResponse,
                          CaptureResponse,
                          ColorSpace, Illuminant, Measurement, TristimulusMeasurement,
                          RetrievalResponse, RetrievalResult, RetrievalError, RetrievalSpecificErrorCode)
from metering_pb2_grpc import MeteringServicer, add_MeteringServicer_to_server
from google.protobuf.duration_pb2 import Duration

def fprint(x, **kwargs):
    print(x, flush=True, **kwargs)

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
            meter.calibrate(wait_for_button_press=False)
        meter.promptForMeasurementPositioning()
        calibration_response = CalibrationResponse()
        # This was just a useful test
        # calibration_response.error.generic_error_code = GenericErrorCode.DEVICE_UNRESPONSIVE
        return calibration_response

    def Capture(self, request, context):
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        raw_estimated_duration = meter.trigger_measurement()
        estimated_duration = Duration()
        estimated_duration.seconds = raw_estimated_duration
        capture_response = CaptureResponse(estimated_duration=estimated_duration)
        # capture_response.estimated_duration = meter.trigger_measurement()
        return capture_response

    @staticmethod
    def _wavelengths_for_retrieved_spectrum(meter):
        min_lambda, max_lambda = meter.spectral_range_supported()
        inc_lambda = meter.spectral_resolution()
        return np.arange(min_lambda, max_lambda+1, inc_lambda).tolist()

    def Retrieve(self, request, context):
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        results = []
        spectral_requested = request.spectral_data_requested
        if spectral_requested:
            fprint("spectral retrieval requested")
        if request.colorimetric_configurations:
            fprint("requested colorimetric configurations:")
            for config in request.colorimetric_configurations:
                fprint(f"{ColorSpace.Name(config.color_space)} {Illuminant.Name(config.illuminant)}")
        if spectral_requested:
            fprint('spectral data requested')
            wavelengths = MeteringService._wavelengths_for_retrieved_spectrum(meter)
            fprint(f"{len(wavelengths)} wavelengths, first {wavelengths[0]}, last {wavelengths[-1]}")
            values = meter.spectral_distribution()
            fprint('spectral data retrieved')
            measurement = Measurement()
            measurement.spectral_data.wavelengths.extend(wavelengths)
            measurement.spectral_data.values.extend(values)
            spectral_result = RetrievalResult(measurement=measurement)
            results.append(spectral_result)
        last_color_space = meter.color_space()
        last_illuminant = meter.illuminant()
        fprint(f"last color space is {ColorSpace.Name(last_color_space)}")
        fprint(f"last illuminant is {Illuminant.Name(last_illuminant)}")
        # probably not worth trying to sort configs to minimize time used in changing params
        if request.colorimetric_configurations:
            for config in request.colorimetric_configurations:
                color_space = config.color_space
                illuminant = config.illuminant
                if last_color_space != color_space:
                    fprint(f"setting color space to {color_space}")
                    meter.set_color_space(color_space)
                    fprint(f"set color space to {color_space}")
                    last_color_space = color_space
                if last_illuminant != illuminant:
                    fprint(f"setting illuminant to {illuminant}")
                    meter.set_illuminant(illuminant)
                    fprint(f"set illuminant to {illuminant}")
                    last_illuminant = illuminant
                data = meter.colorimetry()
                tristimulus_measurement = TristimulusMeasurement()
                tristimulus_measurement.color_space = color_space
                tristimulus_measurement.illuminant = illuminant
                tristimulus_measurement.first = data[0]
                tristimulus_measurement.second = data[1]
                tristimulus_measurement.third = data[2]
                measurement = Measurement(tristimulus_data=tristimulus_measurement)
                # measurement.tristimulus_data = tristimulus_measurement
                colorimetric_result = RetrievalResult(measurement=measurement)
                results.append(colorimetric_result)
        response = RetrievalResponse(results=results)
        return response


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
