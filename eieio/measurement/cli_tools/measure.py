# -*- coding: utf-8 -*-
"""
measure - command-line tool to take spectral and (optionally) colorimetric measurements
==============================

Collects instructions for a spectral_measurement session and executes them.
"""

from socket import gethostname
import sys
import os
import queue
from pathlib import Path
from datetime import timedelta

import numpy as np

import grpc
from services.metering.metering_pb2 import (
    IntegrationMode, Observer, MeasurementMode, ColorSpace, Illuminant,
    Instrument, MeterName,  GenericErrorCode,
    StatusRequest, ConfigurationRequest, CalibrationRequest, CaptureRequest,
    ColorimetricConfiguration, RetrievalRequest, RetrievalResponse)
from services.metering import metering_pb2_grpc
from services.ports import PORT_METERING, PORT_TARGET_COLOR_CHANGING

from eieio.measurement.instructions import Instructions
from utilities.log import Log, LogEvent
from eieio.meter.xrite.i1pro import I1Pro
from eieio.measurement.measurement import Measurement
from eieio.measurement.measurement_group import Group
from eieio.measurement.colorimetry import Colorimetry
from eieio.targets.unreal.live_link_target import UnrealLiveLinkTarget
from eieio.targets.unreal.web_control_api_target import UnrealWebControlApiTarget
from eieio.targets.grpc_based.target_color_changing_client import GrpcControlledTarget
from colour.io.tm2714 import SpectralDistribution_IESTM2714
from colour.io.tm2714 import Header_IESTM2714

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    ''
]

LIVE_LINK_LENS_HOST = '192.168.1.157'
LIVE_LINK_LENS_METADATA_PORT = 40123
QUEUE_WAIT_TIMEOUT_SECONDS = 3


def iestm2714_header(**kwargs):
    make = kwargs.get('make', 'Unknown stimulus generator manufacturer')
    model = kwargs.get('model', 'Unknown stimulus generator model')
    description = kwargs.get('description', 'Unknown stimulus being measured')
    document_creator = kwargs.get('creator', os.path.split(os.path.expanduser('~'))[-1])
    report_date = Log.timestamp()
    unique_identifier = (gethostname() + ' ' + report_date).replace(' ', '_')
    measurement_equipment = kwargs.get('device_type', 'Unknown spectral_measurement device type')['type']
    laboratory = kwargs.get('location', 'Unknown spectral_measurement location')
    report_number = Path(os.getcwd()).stem
    return Header_IESTM2714(manufacturer=make, catalog_number=model, description=description,
                            document_creator=document_creator, unique_identifier=unique_identifier,
                            measurement_equipment=measurement_equipment, laboratory=laboratory,
                            report_number=report_number, report_date=report_date)


def iestm2714_header_from_instructions(instructions):
    return iestm2714_header(make=instructions.sample_make, model=instructions.sample_model,
                            description=instructions.sample_description,
                            device_type=instructions.meter,
                            location=instructions.location)


def iestm2714_sd(header, spectral_quantity='radiance', reflection_geometry='Unknown reflection geometry'):
    return SpectralDistribution_IESTM2714(header=header, spectral_quantity=spectral_quantity,
                                          reflection_geometry=reflection_geometry, bandwidth_FWHM=25)


class Measurer(object):
    """
    Coordinating object for measuring stimuli with a metering device and writing results to storage.

    Attributes
    ----------
    """
    def __init__(self, instructions):
        self._log = None
        self.instructions = instructions
        self._channel = None
        self._client = None
        self._meter_name = None
        self._measurement_group = None
        self._target = None

    def print_if_debug(self, str_):
        if self.instructions.verbose:
            print(str_, flush=True)

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, value):
        self._log = value

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value

    @channel.deleter
    def channel(self):
        del self._channel
        self._channel = None

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @client.deleter
    def client(self):
        del self._client
        self._client = None

    @property
    def meter_name(self):
        return self._meter_name

    @meter_name.setter
    def meter_name(self, value):
        self._meter_name = value

    @meter_name.deleter
    def meter_name(self):
        del self._meter_name
        self._meter_name = None

    @property
    def measurement_group(self):
        return self._measurement_group

    @measurement_group.setter
    def measurement_group(self, value):
        self._measurement_group = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @target.deleter
    def target(self):
        del self._target
        self._target = None

    def _setup_output_dir(self, create_parent_dirs=False, exists_ok=False):
        """
        Creates a directory or verifies the presence of an existing directory into which
        spectral_measurement data will be written, optionally creating intermediate directories
        that don't already exist.

        Returns
        -------
        Path
            Path object corresponding to supplied output_dir pathname.

        Raises
        --------
            FileNotFoundError if create_parent_dirs is False and intermediate directories are missing
            FileExistsError if exists_ok is False and the directory already exists

        """
        p = Path(self.instructions.output_dir)
        if p.exists():
            if not exists_ok:
                raise RuntimeError(f"spectral_measurement base dir `{p}' already exists")
            if not p.is_dir():
                raise FileExistsError(f"spectral_measurement base dir `{p}' exists, but is not a directory")
            else:
                if not os.access(p, os.W_OK):
                    raise ProcessLookupError(f"spectral_measurement base dir `{p}' exists, but is not writable")
        else:
            output_dir_parent_path = p.parent
            if not output_dir_parent_path.exists():
                if not create_parent_dirs:
                    raise RuntimeError(f"parent dir(s) of spectral_measurement base dir `{p}' do not exist")
                p.mkdir(parents=True)
            else:
                p.mkdir()

    @staticmethod
    def pretty_generic_error(generic_error_code, details):
        value = None
        if generic_error_code == GenericErrorCode.MISSING_GENERIC_ERROR_CODE:
            value = 'unparsable generic error: missing generic error code'
        elif generic_error_code == GenericErrorCode.DEVICE_DISCONNECTED:
            value = 'Device disconnected'
        elif generic_error_code == GenericErrorCode.DEVICE_BUSY:
            value = 'Device busy'
        elif generic_error_code == GenericErrorCode.DEVICE_UNRESPONSIVE:
            value = 'Device unresponsive'
        elif generic_error_code == GenericErrorCode.UNCATEGORIZED_ERROR:
            value = 'Uncategorizable error'
        if details:
            value = f"{value}: {details}"
        return value

    @staticmethod
    def pretty_print_calibration_error(error):
        if error.HasField('generic_error_code'):
            return Measurer.pretty_generic_error(error.generic_error_code, error.details)
        if not error.HasField('calibration_specific_error_code'):
            return "unparseable calibration error: neither generic nor calibration_specific"
        # code = error.calibration_specific_error_code
        # At the moment there are no calibration-specific errors, so...
        return "unparseable calibration error: calibration_specific error indicated, but there are no such errors"

    def _setup_measurement_device(self, instructions):
        device_host_and_port = f"{instructions.meter['host']}:{PORT_METERING}"
        self.meter_name = MeterName(name=instructions.meter['name'])
        self.log.add(LogEvent.GRPC_ACTIVITY, f"setting up measurement device with host and port "
                                             f"`{device_host_and_port}'", 'Measurer._setup_measurement_device')
        self.channel = grpc.insecure_channel(device_host_and_port)
        self.client = metering_pb2_grpc.MeteringStub(self.channel)
        # Get and print meter status
        status_request = StatusRequest(meter_name=self.meter_name)
        status_response = self.client.ReportStatus(status_request)
        Measurer.print_meter_description(status_response.description)
        # calibrate if need be
        used_tile = False
        needs_tile_positioning = status_response.description.model.startswith('i1pro') and not used_tile
        needs_target_positioning = True
        for used_and_left in status_response.description.calibrations_used_and_left:
            mode = used_and_left.mode
            left = used_and_left.left
            if left.ToTimedelta() < timedelta(hours=1):
                calibration_request = CalibrationRequest(meter_name=self.meter_name, mode=mode)
                if needs_tile_positioning:
                    I1Pro.prompt_for_calibration_positioning("place i1Pro on tile and press RETURN")
                    needs_tile_positioning = False
                    needs_target_positioning = True
                calibration_response = self.client.Calibrate(calibration_request)
                if calibration_response.HasField('error'):
                    raise RuntimeError(f"{Measurer.pretty_print_calibration_error(calibration_response.error)}")
        if needs_target_positioning:
            I1Pro.prompt_for_target_positioning("orient i1Pro towards target and press RETURN")
        # TODO add configuration request options for path to USB device
        # elif self.meter_type == 'cs2000':
        #     self.device = CS2000(debug=self.instructions.verbose, **meter_params)
        configuration_request = ConfigurationRequest(meter_name=self.meter_name,
                                                     observer=Observer.TWO_DEGREE_1931,
                                                     measurement_mode=MeasurementMode.EMISSIVE,
                                                     illuminant=Illuminant.D65,
                                                     color_space=ColorSpace.CIE_xyY)
        configuration_response = self.client.Configure(configuration_request)
        if configuration_response.error:
            print("---> not everything went well with the configuration request")

    def _setup_target(self):
        target_type = self.instructions.target['type']
        target_params = self.instructions.target['params'] if 'params' in self.instructions.target else None
        if target_type == 'passive':
            return None
        elif target_type == 'unreal_live_link':
            host = target_params['host']
            port = target_params['port']
            queue_wait_timeout = target_params['queue_wait_timeout']
            target_queue = queue.Queue(10)
            return UnrealLiveLinkTarget(host, port, target_queue, queue_wait_timeout=queue_wait_timeout)
        elif target_type == 'unreal_web_control_api':
            host = target_params['host']
            port = target_params['port']
            return UnrealWebControlApiTarget(host, port)
        elif target_type == 'grpc_service':
            host = target_params['host']
            patch_name = target_params['patch_name']
            self.log.add(LogEvent.GRPC_ACTIVITY, f"setting up target at {host}:{PORT_TARGET_COLOR_CHANGING} with name "
                                                 f"`{patch_name}', 'Measurer._setup_target")
            return GrpcControlledTarget(host, patch_name, self.log)
        else:
            raise RuntimeError(f"unknown target type {target_type}")

    def cleanup(self):
        if self.target:
            self.log.add(LogEvent.RESOURCE_DELETIONS, "deleting target")
            del self.target
            self.target = None
            self.log.add(LogEvent.RESOURCE_DELETIONS, "deleted target")
        # if self.session and self.session.contains_unsaved_measurements():
        #     if log:
        #         log.add(LogEvent.RESOURCE_DELETIONS, "saving session")
        #     self.session.save()
        #     if log:
        #         log.add(LogEvent.RESOURCE_DELETIONS, "saved session")
        if self.channel:
            self.log.add(LogEvent.RESOURCE_DELETIONS, "deleting channel")
            del self.channel
            self.log.add(LogEvent.RESOURCE_DELETIONS, "deleted channel")

    # @staticmethod
    # def print_colorimetry(sd):
    #     cap_xyz = sd_to_XYZ(sd)
    #     (x, y) = XYZ_to_xy(cap_xyz)
    #     print(f"\tCIE 1931 XYZ: {cap_xyz[0]:8.4}  {cap_xyz[1]:8.4} {cap_xyz[2]:8.4}", flush=True)
    #     print(f"\tCIE x,y: {x:6.4}, {y:6.4}", flush=True)

    @staticmethod
    def fprint(x, **kwargs):
        print(x, flush=True, **kwargs)

    @staticmethod
    def print_if_not_blank(value, label):
        if value:
            Measurer.fprint(f"{label}: {value}")

    @staticmethod
    def print_meter_description(meter_desc):
        Measurer.print_if_not_blank(meter_desc.name, "name")
        # if meter_desc.HasField('name'):
        #     print(f"name : {meter_desc.name}")
        if meter_desc.instrument != Instrument.MISSING_INSTRUMENT:
            print(f"instrument: {meter_desc.instrument.Name()}")
        Measurer.print_if_not_blank(meter_desc.make, 'make')
        Measurer.print_if_not_blank(meter_desc.model, 'model')
        Measurer.print_if_not_blank(meter_desc.serial_number, 'serial number')
        Measurer.print_if_not_blank(meter_desc.firmware_version, 'firmware version')
        Measurer.print_if_not_blank(meter_desc.sdk_version, 'SDK version')
        Measurer.print_if_not_blank(meter_desc.adapter_version, 'adapter version')
        Measurer.print_if_not_blank(meter_desc.adapter_module_version, 'adapter [Python] module version')
        for measurement_mode in meter_desc.supported_measurement_modes:
            Measurer.print_if_not_blank(MeasurementMode.Name(measurement_mode), 'supported spectral_measurement mode')
        Measurer.print_if_not_blank(meter_desc.current_measurement_mode, 'current spectral_measurement mode')
        for integration_mode in meter_desc.supported_integration_modes:
            Measurer.print_if_not_blank(IntegrationMode.Name(integration_mode), 'supported integration mode')
        Measurer.print_if_not_blank(meter_desc.current_integration_mode, 'current integration mode')
        for measurement_angle in meter_desc.supported_measurement_angles:
            Measurer.print_if_not_blank(measurement_angle, 'supported spectral_measurement angle')
        Measurer.print_if_not_blank(meter_desc.current_measurement_angle, 'current spectral_measurement angle')

    def capture_stimulus(self):
        # capture the stimulus
        self.log.add(LogEvent.METER_TRIGGER, 'about to send capture request')
        capture_request = CaptureRequest(meter_name=self.meter_name)
        self.log.add(LogEvent.METER_TRIGGER, 'send capture request, waiting for capture response')
        capture_response = self.client.Capture(capture_request)
        self.log.add(LogEvent.METER_TRIGGER, 'received capture response')
        if capture_response.estimated_duration:
            self.log.add(LogEvent.METER_TRIGGER, f"estimated time is {capture_response.estimated_duration}")
        else:
            self.log.add(LogEvent.METER_TRIGGER, 'no time estimate (assuming zero)')

    # @staticmethod
    # def pretty_print_spectrum(spectral_measurement):
    #     if spectral_measurement.wavelengths:
    #         for i, wavelength in enumerate(spectral_measurement.wavelengths):
    #             print(f"{wavelength:3}nm: {spectral_measurement.values[i]}")

    # def _process_retrieved_spectrum(self, spectral_measurement, meas_header, patch_number, sample_name, log=None):
    #     sd = iestm2714_sd(meas_header)
    #     sd.wavelengths = spectral_measurement.wavelengths
    #     sd.values = spectral_measurement.values
    #     sd_output_filename = f"sample.{patch_number:04d}.spdx"
    #     sd.path = str(Path(self.instructions.output_dir, sd_output_filename))
    #     print(f"patch {sample_name}: ", end='', flush=True)
    #     self.session.add_spectral_measurement(sd)
    #     self.session.save()
    #     Measurer.pretty_print_spectrum(spectral_measurement)

    # @staticmethod
    # def pretty_print_tristimulus_measurement(tristimulus_measurement):
    #     color_space = ColorSpace.Name(tristimulus_measurement.color_space)
    #     illuminant = Illuminant.Name(tristimulus_measurement.illuminant)
    #     if color_space not in ['CIE_XYZ', 'CIE_xyY', 'RxRyRz', 'RGB', 'Lv_xy', 'Y_xy', 'Lv_T_duv',
    #                            'Dominant_wavelength_and_excitation_purity']:
    #         color_space = f"{color_space} ({illuminant})"
    #     first = float(tristimulus_measurement.first)
    #     second = float(tristimulus_measurement.second)
    #     third = float(tristimulus_measurement.third)
    #     print(f"{color_space} / {illuminant}: {first:5.4f} {second:5.4f} {third:5.4}")

    # def _process_retrieved_tristimulus_measurement(self, tristimulus_measurement,
    #                                                meas_header, patch_number, log=None):
    #     color_space = ColorSpace.Name(tristimulus_measurement.color_space)
    #     illuminant = Illuminant.Name(tristimulus_measurement.illuminant)
    #     component_values = [tristimulus_measurement.first,
    #                         tristimulus_measurement.second,
    #                         tristimulus_measurement.third]
    #     color = ColxColorimetry('2º', color_space, component_values, illuminant)
    #     tsc = Colorimetry_IESTM2714(header=meas_header, colorimetric_quantity='radiance',
    #                                 origin=Origin.MEASURED, colorimetry=color)
    #     safe_color_space = color_space.lower().replace(' ','_')
    #     tsc_output_filename = f"sample.{patch_number:04d}.{safe_color_space}.colx"
    #     tsc.path = str(Path(self.instructions.output_dir, tsc_output_filename))
    #     self.session.add_tristimulus_colorimetry_measurement(tsc)
    #     self.session.save()
    #     self.pretty_print_tristimulus_measurement(tristimulus_measurement)

    def _process_retrieval_response(self, response: RetrievalResponse):
        header = iestm2714_header_from_instructions(self.instructions)
        measurement = Measurement(header=header)
        # first let's gather all the data together
        if response.HasField('spectral_measurement'):
            measurement.values = response.spectral_measurement.values
            measurement.wavelengths = response.spectral_measurement.wavelengths
        else:  # only because TM 2714 doesn't like it when there's no spectral data
            measurement.values = (1.0, 1.0)
            measurement.wavelengths = (380, 780)
        for tristimulus_measurement in response.tristimulus_measurements:
            observer = Observer.Name(tristimulus_measurement.observer)
            color_space = ColorSpace.Name(tristimulus_measurement.color_space)
            illuminant = Illuminant.Name(tristimulus_measurement.illuminant)
            component_values = [tristimulus_measurement.first,
                                tristimulus_measurement.second,
                                tristimulus_measurement.third]
            colorimetry = Colorimetry(observer, color_space, illuminant, component_values, 'measured')
            measurement.insert_colorimetry(colorimetry)
            print(colorimetry)
        return measurement

        # patch_number = sequence_number + 1  # 1-based for user-friendliness
        # # someday figure out how to evaluate a passed f-string inside this loop context
        # # looks crazy hard tho:
        # # https://stackoverflow.com/questions/54700826/how-to-evaluate-a-variable-as-a-python-f-string
        # sample_name = self.instructions.base_measurement_name.replace('{sequence_number}',
        #                                                               f"{patch_number}")
        # sample_name = sample_name.replace('{tmp_dir}', '/var/tmp')

    def _colorimetric_configurations(self):
        cs_map = {'cie xyz': ColorSpace.CIE_XYZ,
                  'cie xyy': ColorSpace.CIE_xyY}
        il_map = {'d65': Illuminant.D65}
        configs = []
        for config_in_instructions in self.instructions.colorimetry:
            color_space = config_in_instructions['color_space'].lower().replace('_', ' ')
            illuminant = config_in_instructions['illuminant'].lower().replace('_', ' ')
            config = ColorimetricConfiguration(color_space=cs_map[color_space], illuminant=il_map[illuminant])
            configs.append(config)
        return configs

    def main_loop(self):
        self.log = Log()
        self.log.event_mask = (LogEvent.GRPC_ACTIVITY | LogEvent.LOW_LEVEL_ERRORS |
                               LogEvent.METER_OPTION_SETTING | LogEvent.METER_OPTION_RETRIEVAL |
                               LogEvent.METER_STATUS | LogEvent.METER_CALIBRATION |
                               LogEvent.METER_CONFIGURATION | LogEvent.METER_TRIGGER |
                               LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL |
                               LogEvent.TARGET_OPTION_SETTING)
        dir_ = self.instructions.output_dir
        group_name = Path(dir_).name
        self.measurement_group = Group(Path(dir_, group_name), missing_ok=True)
        try:
            self._setup_output_dir()
            self.target = self._setup_target()
            self._setup_measurement_device(self.instructions)
            # self.session = Session(self.instructions.output_dir)
            configs = self._colorimetric_configurations()
            for sequence_number, sample in enumerate(self.instructions.sample_sequence):

                # configure the target (if need be; if it's passive, it doesn't show up
                if self.target:
                    rgb = sample['value']
                    name = sample['name']
                    self.target.set_target_stimulus(name, rgb)

                # trigger the spectral_measurement
                self.capture_stimulus()

                # retrieve spectral data and colorimetry
                retrieval_request = RetrievalRequest(meter_name=self.meter_name,
                                                     spectrum_requested=True,
                                                     colorimetric_configurations=configs)
                self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL,
                             "retrieving spectrum and colorimetry")
                retrieval_response = self.client.Retrieve(retrieval_request)
                self.log.add(LogEvent.METER_SPECTRAL_RETRIEVAL | LogEvent.METER_COLORIMETRIC_RETRIEVAL,
                             "processing retrieved spectrum and colorimetry")
                measurement = self._process_retrieval_response(retrieval_response)
                filename = f"sample.{sequence_number}"
                if 'name' in sample:
                    filename = f"{filename}.{sample['name']}"
                filename = f"{filename}.spdx"
                measurement.path = str(Path(dir_, filename))
                measurement.write()
                if dir_ not in self.measurement_group.collections:
                    self.measurement_group.collections[dir_] = {}
                self.measurement_group.collections[dir_][filename] = measurement
        finally:
            self.cleanup()


if __name__ == '__main__':
    main_instructions = Instructions(__name__,
                                     'measure a sequence of stimuli, gathering spectra'
                                     'and (optionally) colorimetry')
    main_instructions.merge_files_and_command_line_args(sys.argv[1:])
    instance = Measurer(main_instructions)
    instance.main_loop()