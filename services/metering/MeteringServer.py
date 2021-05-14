# -*- coding: utf-8 -*-
"""
A meter_desc-access-and-control service using Google protobufs and gRPC
===================

Implements the functions required of a Metering server.

"""

from concurrent import futures
import numpy as np
from signal import signal, SIGINT
from pathlib import Path

import grpc
from google.protobuf.duration_pb2 import Duration

from serial.serialutil import SerialException

# from eieio.meter.meter_errors import UnsupportedMeasurementMode
from metering_pb2 import (IntegrationMode, MeasurementMode,
                          MeterName, MeterDescription,
                          StatusResponse, CalibrationsUsedAndLeft,
                          ConfigurationResponse,
                          CalibrationResponse,
                          CaptureResponse,
                          Observer, ColorSpace, Illuminant, TristimulusMeasurement,
                          RetrievalResponse, SpectralMeasurement)
from metering_pb2_grpc import MeteringServicer, add_MeteringServicer_to_server
from services.ports import PORT_METERING

from utilities.log import Log, LogEvent

from eieio.meter.minolta.cs2000 import CS2000, cs2000_tty_path
from eieio.meter.xrite.i1pro import I1Pro


class MeteringService(MeteringServicer):

    @staticmethod
    def configure_meter(meter):
        meter.set_observer(Observer.TWO_DEGREE_1931)
        meter.set_integration_mode(IntegrationMode.NORMAL_ADAPTIVE)
        meter.set_measurement_mode(MeasurementMode.EMISSIVE)
        meter.set_color_space(ColorSpace.CIE_LAB)
        meter.set_illuminant(Illuminant.D65)

    def __init__(self):
        self._log = None
        self.log = Log()
        self.log.event_mask = (LogEvent.EXTERNAL_API_ENTRY | LogEvent.INTERNAL_API_ENTRY
                               | LogEvent.METER_OPTION_SETTING | LogEvent.METER_OPTION_RETRIEVAL
                               | LogEvent.METER_TRIGGER
                               | LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL)
        I1Pro.populate_registries()
        self._meters = dict()
        for meter_name, _ in I1Pro.meter_names_and_models():
            meter = I1Pro(meter_name=meter_name)
            meter.set_log_options(LogEvent.EVERYTHING)
            # meter.set_log_options(LogEvent.EXTERNAL_API_ENTRY | LogEvent.INTERNAL_API_ENTRY
            #                       | LogEvent.METER_OPTION_SETTING | LogEvent.METER_OPTION_RETRIEVAL
            #                       | LogEvent.METER_TRIGGER
            #                       | LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL)
            MeteringService.configure_meter(meter)
            self.meters[meter_name] = meter
        if Path(cs2000_tty_path()):
            try:
                self.meters['cs2000a'] = CS2000(debug=True)
            except SerialException:
                self.log.add(LogEvent.INTERNAL_API_ENTRY, 'could not find Minolta', 'MeteringService __init__')

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, value):
        self._log = value

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
            self.log.add(LogEvent.METER_TRIGGER, f"could not find meter named `{meter_name}",
                         'MeteringServer.Configure')
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        if request.HasField('integration_mode'):
            self.log.add(LogEvent.METER_OPTION_SETTING, f"setting integration mode to "
                                                        f"{IntegrationMode.Name(request.integration_mode)}",
                         'MeteringServer.Configure')
            meter.set_integration_mode(request.integration_mode)
        if request.HasField('observer'):
            self.log.add(LogEvent.METER_OPTION_SETTING, f"setting observer to "
                                                        f"{Observer.Name(request.observer)}",
                         'MeteringServer.Configure')
            meter.set_observer(request.observer)
        if request.HasField('measurement_mode'):
            self.log.add(LogEvent.METER_OPTION_SETTING, f"setting measurement mode to "
                                                        f"{MeasurementMode.Name(request.measurement_mode)}",
                         'MeteringServer.Configure')
            meter.set_measurement_mode(request.measurement_mode)
        if request.HasField('illuminant'):
            self.log.add(LogEvent.METER_OPTION_SETTING, f"setting illuminant to "
                                                        f"{Illuminant.Name(request.illuminant)}",
                         'MeteringServer.Configure')
            meter.set_illuminant(request.illuminant)
        if request.HasField('color_space'):
            self.log.add(LogEvent.METER_OPTION_SETTING, f"setting color space to "
                                                        f"{ColorSpace.Name(request.color_space)}",
                         'MeteringServer.Configure')
            meter.set_color_space(request.color_space)
        return ConfigurationResponse()

    def ReportStatus(self, request, context):
        self.log.add(LogEvent.METER_OPTION_RETRIEVAL, 'getting status', 'MeteringServer.ReportStatus')
        print('here I am', flush=True)
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
            self.log.add(LogEvent.METER_TRIGGER, f"could not find meter named `{meter_name}", 'MeteringServer.Capture')
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        self.log.add(LogEvent.METER_TRIGGER, 'triggering measurement', 'MeteringServer.Capture')
        raw_estimated_duration = meter.trigger_measurement()
        estimated_duration = Duration()
        self.log.add(LogEvent.METER_TRIGGER, f"estimated duration of measurement: {estimated_duration}")
        estimated_duration.seconds = raw_estimated_duration
        capture_response = CaptureResponse(estimated_duration=estimated_duration)
        return capture_response

    @staticmethod
    def _wavelengths_for_retrieved_spectrum(meter):
        min_lambda, max_lambda = meter.spectral_range_supported()
        inc_lambda = meter.spectral_resolution()
        return list(np.arange(min_lambda, max_lambda+1, inc_lambda))

    def Retrieve(self, request, context):
        self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL,
                     "retrieving results", "MeteringService.Retrieve")
        meter_name = request.meter_name.name
        if meter_name not in self.meters.keys():
            self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL,
                         f"could not find meter named `{meter_name}")
            context.abort(grpc.StatusCode.NOT_FOUND, f"No meter_desc named `{meter_name}' found")
        meter = self.meters[meter_name]
        spectral_requested = request.spectrum_requested
        if request.colorimetric_configurations:
            self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, "requested colorimetric configurations:",
                         'MeteringService.Retrieve')
            for config in request.colorimetric_configurations:
                self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"\t{Observer.Name(config.observer)} "
                                                             f"{ColorSpace.Name(config.color_space)} "
                                                             f"{Illuminant.Name(config.illuminant)}",
                             'MeteringService.Retrieve')
        results = {}
        if spectral_requested:
            self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL, "retrieving spectral data from meter", "MeteringService.Retrieve")
            wavelengths = MeteringService._wavelengths_for_retrieved_spectrum(meter)
            self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL, f"{len(wavelengths)} wavelengths, first {wavelengths[0]}, "
                                                      f"last {wavelengths[-1]}",
                         'MeteringService.Retrieve')
            values = meter.spectral_distribution()
            self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL, 'spectral data retrieved', 'MeteringService.Retrieve')
            spectral_measurement = SpectralMeasurement()
            spectral_measurement.wavelengths.extend(wavelengths)
            spectral_measurement.values.extend(values)
            results['spectral_measurement'] = spectral_measurement
        last_observer = Observer.TWO_DEGREE_1931
        last_color_space = ColorSpace.CIE_xyY
        last_illuminant = meter.illuminant()
        colorimetry = []
        # probably not worth trying to sort configs to minimize time used in changing params
        if request.colorimetric_configurations:
            for config in request.colorimetric_configurations:
                observer = config.observer
                color_space = config.color_space
                illuminant = config.illuminant
                if last_observer != observer:
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"setting observer to {observer}",
                                 'MeteringService.Retrieve')
                    meter.set_observer(observer)
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"set observer to {observer}",
                                 'MeteringService.Retrieve')
                    last_observer = observer
                if last_color_space != color_space:
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"setting color space to {color_space}",
                                 'MeteringService.Retrieve')
                    meter.set_color_space(color_space)
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"set color space to {color_space}",
                                 'MeteringService.Retrieve')
                    last_color_space = color_space
                if last_illuminant != illuminant:
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"setting illuminant to {illuminant}",
                                 'MeteringService.Retrieve')
                    meter.set_illuminant(illuminant)
                    self.log.add(LogEvent.METER_COLORIMETRIC_RETRIEVAL, f"set illuminant to {illuminant}",
                                 'MeteringService.Retrieve')
                    last_illuminant = illuminant
                data = meter.colorimetry()
                tristimulus_measurement = TristimulusMeasurement()
                tristimulus_measurement.observer = observer
                tristimulus_measurement.color_space = color_space
                tristimulus_measurement.illuminant = illuminant
                tristimulus_measurement.first = data[0]
                tristimulus_measurement.second = data[1]
                tristimulus_measurement.third = data[2]
                colorimetry.append(tristimulus_measurement)
            if colorimetry:
                results['tristimulus_measurements'] = colorimetry
        print('look at the results dict here')
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
        self.grpc_server.add_insecure_port(f"[::]:{PORT_METERING}")
        self.grpc_server.start()
        signal(SIGINT, lambda signum, _: self.shutdown_service())
        self.grpc_server.wait_for_termination()


if __name__ == '__main__':
    print('Running metering server...', flush=True)
    grpc_server = MeteringServer()
    grpc_server.serve()
