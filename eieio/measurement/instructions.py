# -*- coding: utf-8 -*-
"""
Instructions - the parameters and sequence of a measurement session
==============================

Collects together a measurement session's device name and parameters, input sequence,
output destination, and any pre- and post-frame hooks.
"""

import os
import sys
import datetime
import argparse as ap
from pathlib import Path
import toml
from eieio.meter.meter_abstractions import Mode

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Instructions'
]

EIEIO_CONFIG = ".measurement_defaults.toml"
NAMED_MODES = {'ambient': Mode.ambient, 'emissive': Mode.emissive, 'reflective': Mode.reflective}


class Instructions(object):
    """
    Represent instructions for a measurement run.

    Attributes
    ----------
    -   :attr:`~eieio.measurement.instructions.output_dir`
    -   :attr:`~eieio.measurement.instructions.device_type`
    -   :attr:`~eieio.measurement.instructions.mode`
    """
    def __init__(self, source, desc):
        self._source = source
        self._desc = desc
        self._parser = None
        self._args = None
        self.device_type = None
        self.mode = None
        self.colorspace = None
        self.base_measurement_name = None
        self.sample_make = None
        self.sample_model = None
        self.sample_description = None
        self.location = None
        self.sequence_file = None
        self.frame_preflight = None
        self.frame_postflight = None
        self.output_dir = None
        self.create_parent_dirs = False
        self.output_dir_exists_ok = False
        self.verbose = False

    def merge_eieio_file_defaults(self):
        config_path = Path(EIEIO_CONFIG).resolve()
        if config_path.exists():
            try:
                default_dict = toml.load(str(config_path))
                if 'measurement' not in default_dict:
                    return
                meas_dict = default_dict['measurement']
                for meas_key in self.__dict__.keys():
                    # ['device_type', 'mode', 'colorspace', 'base_measurement_name',
                    #              'sequence_file', 'frame_preflight', 'frame_postflight',
                    #              'output_dir', 'create_parent_dirs', 'output_dir_exists_ok']:
                    if meas_key in meas_dict:
                        setattr(self, meas_key, meas_dict[meas_key])
            except toml.decoder.TomlDecodeError as e:
                print(f"error decoding EIEIO config file: {e}")
                return

    @staticmethod
    def current_timestamp():
        return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_T%H%M%S')

    @staticmethod
    def default_dir():
        return str(Path(os.getcwd(), Instructions.current_timestamp()))

    def merge_command_line_args(self, arg_source=sys.argv[1:]):
        self._parser = ap.ArgumentParser()
        # TODO make device_choices extensible by looking in a directory at runtime
        # say by looking for modules in the eieio.meter package that conform fully to
        # the eieio.meter.meter_abstractions abstract base class
        device_choices = ['i1pro', 'sekonic']
        # str.lower courtesy of https://stackoverflow.com/questions/27616778/case-insensitive-argparse-choices
        self._parser.add_argument('--device_type', '-d', type=str.lower, choices=device_choices, required=True)
        self._parser.add_argument('--mode', '-m', type=str.lower, choices=['emissive', 'ambient', 'reflective'],
                                  default='emissive')
        self._parser.add_argument('--colorspace', '-c', type=str.lower, choices=['xyz', 'lab'], default='xyz')
        self._parser.add_argument('--base_measurement_name', '-b', required=True)
        self._parser.add_argument('--sample_make', required=True)
        self._parser.add_argument('--sample_model', required=True)
        self._parser.add_argument('--sample_description', required=True)
        self._parser.add_argument('--location', required=True)
        self._parser.add_argument('--sequence_file', '-s', required=True)
        self._parser.add_argument('--frame_preflight')
        self._parser.add_argument('--frame_postflight')
        self._parser.add_argument('--output_dir', '-o', default=Instructions.default_dir())
        self._parser.add_argument('--create_parent_dirs', '-p', action='store_true')
        self._parser.add_argument('--exists_ok', '-e', action='store_true')
        self._parser.add_argument('--verbose', '-v', action='store_true')
        self._args = self._parser.parse_args(arg_source)
        # expose to outside world
        if self._args.device_type:
            self.device_type = self._args.device_type
        if self._args.mode:
            mode_dict = {'emissive': Mode.emissive, 'ambient': Mode.ambient, 'reflective':Mode.reflective}
            self.mode = mode_dict[self._args.mode]
        if self._args.colorspace:
            self.colorspace = self._args.colorspace
        if self._args.base_measurement_name:
            self.base_measurement_name = self._args.base_measurement_name
        if self._args.sequence_file:
            self.sequence_file = self._args.sequence_file
        if self._args.sample_make:
            self.sample_make = self._args.sample_make
        if self._args.sample_model:
            self.sample_model = self._args.sample_model
        if self._args.sample_description:
            self.sample_description = self._args.sample_description
        if self._args.location:
            self.location = self._args.location
        if self._args.frame_preflight:
            self.frame_preflight = self._args.frame_preflight
        if self._args.frame_postflight:
            self.frame_postflight = self._args.frame_postflight
        if self._args.output_dir:
            self.output_dir = self._args.output_dir
        if self._args.create_parent_dirs:
            self.create_parent_dirs = self._args.create_parent_dirs
        if self._args.exists_ok:
            self.output_dir_exists_ok = self._args.exists_ok
        if self._args.verbose:
            self.verbose = self._args.verbose

    def consistency_check(self):
        # TODO if the device is a sekonic, make sure it's a file:/path URL
        # really you want to pass that to an argument validation class method on Sekonic, no?
        self._parser.mode = NAMED_MODES[self._parser.mode]
        return True, ''


if __name__ == '__main__':
    desc = 'measure a sequence of stimuli, gathering spectra and (optionally) colorimetry'
    instructions = Instructions(__file__, desc)
    print(instructions)
    consistent, issues = instructions.consistency_check()
    if not consistent:
        print('the following issues were detected in extended argument consistency checking:')
        print(issues)
