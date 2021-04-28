# -*- coding: utf-8 -*-
"""
A meter_desc-access-and-control service using Google protobufs and gRPC
===================

Implements the functions required of a Metering server.

"""

from concurrent import futures
import numpy as np
from signal import signal, SIGINT

import grpc

from eieio.meter.xrite.i1pro import I1Pro
# from eieio.meter.meter_errors import UnsupportedMeasurementMode
from metering_pb2 import (Observer, IntegrationMode, MeasurementMode,
                          MeterName, MeterDescription,
                          StatusResponse, CalibrationsUsedAndLeft,
                          ConfigurationResponse,
                          CalibrationResponse,
                          CaptureResponse,
                          ColorSpace, Illuminant, TristimulusMeasurement,
                          RetrievalResponse, SpectralMeasurement)
from metering_pb2_grpc import MeteringServicer, add_MeteringServicer_to_server
from google.protobuf.duration_pb2 import Duration

LOG_NOTHING = 0
LOG_EXTERNAL_API_ENTRY = (1 << 0)
LOG_INTERNAL_API_ENTRY = (1 << 1)
LOG_REGISTRY_ACTIVITY = (1 << 2)
LOG_OPTION_SETTING = (1 << 3)
LOG_OPTION_RETRIEVAL = (1 << 4)
LOG_COLORIMETRY_RETRIEVAL = (1 << 5)
LOG_ERRORS_FROM_LOWER_LEVEL = (1 << 6)


def fprint(x, **kwargs):
    print(x, flush=True, **kwargs)


class MeteringService(MeteringServicer):

    @staticmethod
    def configure_meter(meter):
        meter.set_observer(Observer.TWO_DEGREE_1931)
        meter.set_integration_mode(IntegrationMode.NORMAL_ADAPTIVE)
        meter.set_measurement_mode(MeasurementMode.EMISSIVE)
        meter.set_color_space(ColorSpace.CIE_LAB)
        meter.set_illuminant(Illuminant.D65)

    def __init__(self):
        I1Pro.populate_registries()
        self._meters = dict()
        for meter_name, _ in I1Pro.meter_names_and_models():
            meter = I1Pro(meter_name=meter_name)
            meter.set_log_options(LOG_EXTERNAL_API_ENTRY | LOG_INTERNAL_API_ENTRY | LOG_OPTION_SETTING | LOG_OPTION_RETRIEVAL | LOG_COLORIMETRY_RETRIEVAL | LOG_ERRORS_FROM_LOWER_LEVEL)
            MeteringService.configure_meter(meter)
            self.meters[meter_name] = meter

    @property
    def meters(self):
        return self._meters

    def shutdown(self):
        for meter in self.meters.values():
            meter.close()

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
        calibrations_used_and_left = []
        for mode in supported_measurement_modes:
            meter.set_measurement_mode(mode)
            used, left = meter.calibration_used_and_left()
            used_and_left = CalibrationsUsedAndLeft(mode=mode, used=used, left=left)
            calibrations_used_and_left.append(used_and_left)
        supported_observers = meter.observers()
        current_observer = meter.observer()
        supported_integration_modes = meter.integration_modes()
        current_integration_mode = meter.integration_mode()
        supported_measurement_angles = meter.measurement_angles()
        current_measurement_angle = meter.measurement_angle()
        supported_color_spaces = meter.color_spaces()
        current_color_space = meter.color_space()
        supported_illuminants = meter.illuminants()
        current_illuminant = meter.illuminant()
        return MeterDescription(name=MeterName(name=name),
                                make=make, model=model,
                                serial_number=serial_number,
                                firmware_version=firmware_version,
                                sdk_version=sdk_version,
                                adapter_version=adapter_version,
                                adapter_module_version=adapter_module_version,
                                supported_measurement_modes=supported_measurement_modes,
                                current_measurement_mode=current_measurement_mode,
                                calibrations_used_and_left=calibrations_used_and_left,
                                supported_observers=supported_observers,
                                current_observer=current_observer,
                                supported_integration_modes=supported_integration_modes,
                                current_integration_mode=current_integration_mode,
                                supported_measurement_angles=supported_measurement_angles,
                                current_measurement_angle=current_measurement_angle,
                                supported_color_spaces=supported_color_spaces,
                                current_color_space=current_color_space,
                                supported_illuminants=supported_illuminants,
                                current_illuminant=current_illuminant)

    def Configure(self, request, context):
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        if request.HasField('integration_mode'):
            meter.set_integration_mode(request.integration_mode)
        if request.HasField('observer'):
            meter.set_observer(request.observer)
        if request.HasField('measurement_mode'):
            meter.set_measurement_mode(request.measurement_mode)
        if request.HasField('illuminant'):
            meter.set_illuminant(request.illuminant)
        if request.HasField('color_space'):
            meter.set_color_space(request.color_space)
        return ConfigurationResponse()

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
        # if there's not a specific calibration that someone had in mind,
        # then calibrate everything the meter's got.
        for measurement_mode in [request.mode] if request.mode else meter.measurement_modes():
            meter.set_measurement_mode(measurement_mode)
            meter.calibrate(wait_for_button_press=False)
        return CalibrationResponse()

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
        return list(np.arange(min_lambda, max_lambda+1, inc_lambda))

    def examine_results(self, **kwargs):
        if kwargs.get('spectral_measurement'):
            specMeas = kwargs['spectral_measurement']
            print(f'saw spectral measurement')
        if kwargs.get('tristimulus_measurements'):
            colorimetry = kwargs['tristimulus_measurements']
            print(f"saw {len(colorimetry)} colorimetric measurements")
            # for spectral_measurement in colorimetry:
            #     pr_cs = ColorSpace.Name(spectral_measurement.color_space)
            #     pr_il = Illuminant.Name(spectral_measurement.illuminant)
            #     first = float(spectral_measurement.first)
            #     second = float(spectral_measurement.second)
            #     third = float(spectral_measurement.third)
            #     print(f"  {pr_cs} / {pr_il}:{first:6.4f} {second:6.4fF} {third:6.4f}")

    def Retrieve(self, request, context):
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        spectral_requested = request.spectrum_requested
        # if spectral_requested:
        #     fprint("spectral retrieval requested")
        if request.colorimetric_configurations:
            fprint("requested colorimetric configurations:")
            for config in request.colorimetric_configurations:
                fprint(f"{ColorSpace.Name(config.color_space)} {Illuminant.Name(config.illuminant)}")
        results = {}
        if spectral_requested:
            # fprint('spectral data requested')
            wavelengths = MeteringService._wavelengths_for_retrieved_spectrum(meter)
            fprint(f"{len(wavelengths)} wavelengths, first {wavelengths[0]}, last {wavelengths[-1]}")
            values = meter.spectral_distribution()
            # fprint('spectral data retrieved')
            spectral_measurement = SpectralMeasurement()
            spectral_measurement.wavelengths.extend(wavelengths)
            spectral_measurement.values.extend(values)
            results['spectral_measurement'] = spectral_measurement
        last_color_space = meter.color_space()
        last_illuminant = meter.illuminant()
        # fprint(f"last color space is {ColorSpace.Name(last_color_space)}")
        # fprint(f"last illuminant is {Illuminant.Name(last_illuminant)}")
        colorimetry = []
        # probably not worth trying to sort configs to minimize time used in changing params
        if request.colorimetric_configurations:
            for config in request.colorimetric_configurations:
                color_space = config.color_space
                illuminant = config.illuminant
                if last_color_space != color_space:
                    # fprint(f"setting color space to {color_space}")
                    meter.set_color_space(color_space)
                    # fprint(f"set color space to {color_space}")
                    last_color_space = color_space
                if last_illuminant != illuminant:
                    # fprint(f"setting illuminant to {illuminant}")
                    meter.set_illuminant(illuminant)
                    # fprint(f"set illuminant to {illuminant}")
                    last_illuminant = illuminant
                data = meter.colorimetry()
                tristimulus_measurement = TristimulusMeasurement()
                tristimulus_measurement.color_space = color_space
                tristimulus_measurement.illuminant = illuminant
                tristimulus_measurement.first = data[0]
                tristimulus_measurement.second = data[1]
                tristimulus_measurement.third = data[2]
                colorimetry.append(tristimulus_measurement)
            if colorimetry:
                results['tristimulus_measurements'] = colorimetry
        self.examine_results(**results)
        response = RetrievalResponse(spectral_measurement=spectral_measurement,
                                     tristimulus_measurements=colorimetry)
        return response


class MeteringServer(object):
    def __init__(self):
        self.grpc_server = None
        self.metering_service = None

    def shutdown_service(self):
        self.metering_service.shutdown()
        all_rpcs_done_event = self.grpc_server.stop(30)
        all_rpcs_done_event.wait(30)

    def serve(self):
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.metering_service = MeteringService()
        add_MeteringServicer_to_server(self.metering_service, self.grpc_server)
        self.grpc_server.add_insecure_port('[::]:50051')
        self.grpc_server.start()
        signal(SIGINT, lambda signum, _: self.shutdown_service())
        self.grpc_server.wait_for_termination()


if __name__ == '__main__':
    print('Running metering server...', flush=True)
    grpc_server = MeteringServer()
    grpc_server.serve()
