# -*- coding: utf-8 -*-
"""
measure - command-line tool to take spectral and (optionally) colorimetric measurements
==============================

Collects instructions for a measurement session and executes them.
"""

from socket import gethostname
import sys
import os
import queue
from time import sleep
from pathlib import Path

from eieio.measurement.instructions import Instructions
from eieio.meter.xrite.i1pro import I1Pro
from eieio.meter.minolta.cs2000 import CS2000
from eieio.measurement.session import MeasurementSession
from eieio.measurement.colorimetry import Colorimetry_IESTM2714, Colorimetry, Origin
from eieio.targets.unreal.live_link_target import UnrealLiveLinkTarget
from eieio.targets.unreal.web_control_api_target import UnrealWebControlApiTarget
from colour.io.tm2714 import SpectralDistribution_IESTM2714
from colour.io.tm2714 import Header_IESTM2714
from colour.colorimetry.spectrum import SpectralShape
from colour.colorimetry.tristimulus_values import sd_to_XYZ
from colour.models.cie_xyy import XYZ_to_xy

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
LIVE_LINK_TARGET_SETTLE_SECONDS = 3
QUEUE_WAIT_TIMEOUT_SECONDS = 3


def iestm2714_header(**kwargs):
    make = kwargs.get('make', 'Unknown stimulus generator manufacturer')
    model = kwargs.get('model', 'Unknown stimulus generator model')
    description = kwargs.get('description', 'Unknown stimulus being measured')
    document_creator = kwargs.get('creator', os.path.split(os.path.expanduser('~'))[-1])
    report_date = MeasurementSession.timestamp()
    unique_identifier = (gethostname() + ' ' + report_date).replace(' ', '_')
    measurement_equipment = kwargs.get('device_type', 'Unknown measurement device type')['type']
    laboratory = kwargs.get('location', 'Unknown measurement location')
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
    -   :attr:`~eieio.cli_tools.measure.Measurer.device`
    """
    def __init__(self, instructions):
        self.instructions = instructions
        self._device = None
        self._target = None
        self._session = None

    def print_if_debug(self, str_):
        if self.instructions.verbose:
            print(str_, flush=True)

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @device.deleter
    def device(self):
        del self._device
        self._device = None

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

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @session.deleter
    def session(self):
        del self._session
        self._session = None

    def _setup_output_dir(self, create_parent_dirs=False, exists_ok=False):
        """
        Creates a directory or verifies the presence of an existing directory into which
        measurement data will be written, optionally creating intermediate directories
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
                raise RuntimeError(f"measurement base dir `{p}' already exists")
            if not p.is_dir():
                raise FileExistsError(f"measurement base dir `{p}' exists, but is not a directory")
            else:
                if not os.access(p, os.W_OK):
                    raise ProcessLookupError(f"measurement base dir `{p}' exists, but is not writable")
        else:
            output_dir_parent_path = p.parent
            if not output_dir_parent_path.exists():
                if not create_parent_dirs:
                    raise RuntimeError(f"parent dir(s) of measurement base dir `{p}' do not exist")
                p.mkdir(parents=True)
            else:
                p.mkdir()

    def setup_measurement_device(self, device_type, device_params=None):
        if device_type.lower() == 'i1pro':
            self.device = I1Pro()
        elif device_type == 'cs2000':
            self.device = CS2000(debug=self.instructions.verbose, **device_params)
        lambda_low, lambda_high = self.device.spectral_range_supported()
        lambda_inc = self.device.spectral_resolution()[0]
        self.device.set_measurement_mode(self.instructions.mode)
        self.device.calibrate(wait_for_button_press=True)
        self.print_if_debug('\ndevice calibrated')
        if device_type.lower() == "i1pro":
            print("position i1Pro so it is facing target and press RETURN", flush=True)
            input()
        return SpectralShape(lambda_low, lambda_high, lambda_inc)

    def setup_target(self, target_type, target_params):
        if target_type == 'passive':
            pass
        elif target_type == 'unreal_live_link':
            host = target_params['host']
            port = target_params['port']
            queue_wait_timeout = target_params['queue_wait_timeout']
            target_queue = queue.Queue(10)
            self.target = UnrealLiveLinkTarget(host, port, target_queue, queue_wait_timeout=queue_wait_timeout)
        elif target_type == 'unreal_web_control_api':
            host = target_params['host']
            port = target_params['port']
            self.target = UnrealWebControlApiTarget(host, port)
        else:
            raise RuntimeError(f"unknown target type {target_type}")

    def cleanup(self):
        if self.target:
            if self.instructions.verbose:
                print("deleting target")
            del self.target
            self.target = None
            if self.instructions.verbose:
                print("deleted target")
        if self.device:
            if self.instructions.verbose:
                print("deleting device")
            del self.device
            self.device = None
            if self.instructions.verbose:
                print("deleted device")

    def main_loop(self):
        try:
            self._setup_output_dir()
            meter_type = self.instructions.meter['type']
            meter_params = self.instructions.meter.get('params', None)
            spectral_shape = self.setup_measurement_device(meter_type, meter_params)
            target_type = self.instructions.target['type']
            target_params = self.instructions.target['params'] if 'params' in self.instructions.target else None
            self.setup_target(target_type, target_params)
            self.session = MeasurementSession(self.instructions.output_dir)
            patch_number = 1
            for sequence_number, sample in enumerate(self.instructions.sample_sequence):
                sample_colorspace = sample['space']
                sample_values = sample['value']
                # TODO figure out how to evaluate a passed f-string inside this loop context
                # looks crazy hard tho:
                # https://stackoverflow.com/questions/54700826/how-to-evaluate-a-variable-as-a-python-f-string
                sample_name = self.instructions.base_measurement_name.replace('{sequence_number}',
                                                                              f"{sequence_number}")
                sample_name = sample_name.replace('{tmp_dir}', '/var/tmp')
                # TODO refactor this mess out to target class
                if self.target:
                    self.target.set_target_stimulus(sample_colorspace, sample_values)
                    print("waiting for target to settle...", end='', flush=True)
                    sleep(LIVE_LINK_TARGET_SETTLE_SECONDS)
                    print("assuming target has settled", flush=True)
                meas_header = iestm2714_header_from_instructions(self.instructions)
                sd = iestm2714_sd(meas_header)
                print(f"patch {sample_name}: ", end='', flush=True)
                self.device.trigger_measurement()
                # color = i1ProAdapter.measuredColorimetry()
                # entry = "%s %.4f %.4f %.4f" % (patch, color[0], color[1], color[2])
                values = self.device.spectral_distribution()
                sd.wavelengths = spectral_shape.range()
                sd.values = values
                sd_output_filename = f"sample.{patch_number:04d}.spdx"
                sd.path = str(Path(self.instructions.output_dir, sd_output_filename))
                cap_xyz = sd_to_XYZ(sd)
                (x, y) = XYZ_to_xy(cap_xyz)
                print(f"\tCIE 1931 XYZ: {cap_xyz[0]:8.4}  {cap_xyz[1]:8.4} {cap_xyz[2]:8.4}", flush=True)
                print(f"\tCIE x,y: {x:6.4}, {y:6.4}", flush=True)
                color = Colorimetry('2º', 'CIE XYZ', cap_xyz)
                tsc = Colorimetry_IESTM2714(header=meas_header, colorimetric_quantity='radiance',
                                            origin=Origin.MEASURED, colorimetry=color)
                tsc_output_filename = f"sample.{patch_number:04d}.colx"
                tsc.path = str(Path(self.instructions.output_dir, tsc_output_filename))
                self.session.add_spectral_measurement(sd)
                self.session.save()
                self.session.add_tristimulus_colorimetry_measurement(tsc)
                self.session.save()
                print()
                patch_number += 1
        finally:
            if self.session and self.session.contains_unsaved_measurements():
                self.session.save()
            self.cleanup()


if __name__ == '__main__':
    main_instructions = Instructions(__name__,
                                     'measure a sequence of stimuli, gathering spectra'
                                     'and (optionally) colorimetry')
    main_instructions.merge_files_and_command_line_args(sys.argv[1:])
    instance = Measurer(main_instructions)
    instance.main_loop()
