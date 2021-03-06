# -*- coding: utf-8 -*-
"""
Instructions - the parameters and sequence of a measurement run
==============================

Collects together a measurement run's device name and parameters, input sequence,
output destination, and any pre- and post-frame hooks.
"""

from os import getcwd
from os.path import expanduser
import sys
import datetime
import argparse as ap
from pathlib import Path

from services.metering.metering_pb2 import MeasurementMode
from utilities.english import oxford_join

import toml

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


class Instructions(object):
    """
    Represent instructions for a spectral_measurement run.

    Parameters
    ----------
    source : unicode
        information about the caller (e.g. a filename, __file__, __main__, etc.)
    desc : unicode
        a short description of what the instructions are for (e.g. measure LED wall)

    Attributes
    ----------
    -   :attr:`~eieio.spectral_measurement.instructions.sequence_file`
    -   :attr:`~eieio.spectral_measurement.instructions.location`
    -   :attr:`~eieio.spectral_measurement.instructions.sample_make`
    -   :attr:`~eieio.spectral_measurement.instructions.sample_model`
    -   :attr:`~eieio.spectral_measurement.instructions.sample_description`
    -   :attr:`~eieio.spectral_measurement.instructions.meter_desc`
    -   :attr:`~eieio.spectral_measurement.instructions.mode`
    -   :attr:`~eieio.spectral_measurement.instructions.colorspace`
    -   :attr:`~eieio.spectral_measurement.instructions.output_dir`
    -   :attr:`~eieio.spectral_measurement.instructions.sample_sequence`
    -   :attr:`~eieio.spectral_measurement.instructions.frame_preflight`
    -   :attr:`~eieio.spectral_measurement.instructions.frame_postflight`
    -   :attr:`~eieio.spectral_measurement.instructions.create_parent_dirs`
    -   :attr:`~eieio.spectral_measurement.instructions.output_dir_exists_ok`
    -   :attr:`~eieio.spectral_measurement.instructions.base_measurement_name`
    -   :attr:`~eieio.spectral_measurement.instructions.verbose`

    Methods
    -------
    -   :meth:`~eieio.spectral_measurement.instructions.Instructions.__init__`
    -   :meth:`~eieio.spectral_measurement.instructions.Instructions.merge_files_and_command_line_args`
    -   :meth:`~eieio.spectral_measurement.instructions.Instructions.consistency_check`
    """
    def __init__(self, source, desc):
        self._source = source
        self._desc = desc
        self._parser = None
        self._args = None
        self.sequence_file = None
        self.location = None
        self.sample_make = None
        self.sample_model = None
        self.sample_description = None
        self.meter = None
        self.mode = None
        self.colorspace = None
        self.output_dir = None
        self.sample_sequence = None
        self.frame_preflight = None
        self.frame_postflight = None
        self.create_parent_dirs = False
        self.output_dir_exists_ok = False
        self.base_measurement_name = None
        self.verbose = False

    def _merge_if_present(self, content, source_desc):
        if 'verbose' in content:  # up front so we know to be verbose in arg processing
            self.verbose = True
        key_attr_dicts_by_table = {'context': {'location': 'location', 'target': 'target'},
                                   'input': {'sample_make': 'sample_make', 'sample_model': 'sample_model',
                                             'sample_description': 'sample_description'},
                                   'device': {'meter': 'meter', 'mode': 'mode'},
                                   'output': {'colorimetry': 'colorimetry', 'dir': 'output_dir'},
                                   'samples': {'sequence_preflight': 'sequence_preflight',
                                               'sample_sequence': 'sample_sequence',
                                               'frame_preflight': 'frame_preflight',
                                               'name_pattern': 'base_measurement_name',
                                               'frame_postflight': 'frame_postflight'}}
        # TODO refactor when less tired
        for section, key_attr_dict in key_attr_dicts_by_table.items():
            if section in content:
                for key, attr in key_attr_dict.items():
                    if key in content[section]:
                        value = content[section][key]
                        setattr(self, attr, value)
                        if self.verbose:
                            if attr == 'samples.sequence':
                                print(f"loaded sequence of {len(value)} samples from {source_desc}")
                            else:
                                print(f"overrode setting of `{attr}' with `{value}' from {source_desc}")
        for section, key_attr_dict in {'output': {'create_parent_dirs': 'create_parent_dirs',
                                                  'output_dir_exists_ok': 'output_dir_exists_ok'}}.items():
            if section in content:
                for key, attr in key_attr_dict.items():
                    if key in content[section]:
                        setattr(self, attr, True)
                        if self.verbose:
                            print(f"set `{attr}' to True from {source_desc}")

    def _merge_config_file_defaults(self, config_path, source_desc):
        if config_path.exists():
            try:
                content = toml.load(str(config_path))
                self._merge_if_present(content, source_desc)
            except toml.decoder.TomlDecodeError as e:
                print(f"error decoding EIEIO config file: {e}")

    def _merge_all_files_defaults(self, sequence_path, sequence_path_desc):
        home = expanduser('~')
        launch_dir = getcwd()
        self._merge_config_file_defaults(Path(home, '.eieio.toml').resolve(), '~/.eieio.toml')
        self._merge_config_file_defaults(Path(launch_dir, '.eieio.toml').resolve(), './.eieio.toml')
        self._merge_config_file_defaults(Path(sequence_path), sequence_path_desc)

    @staticmethod
    def _current_timestamp():
        return datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_T%H%M%S')

    @staticmethod
    def _default_dir():
        return str(Path(getcwd(), Instructions._current_timestamp()))

    def merge_files_and_command_line_args(self, arg_source=None):
        if not arg_source:
            arg_source = sys.argv[1:]  # avoid mutability warning from def decl of default
        self._parser = ap.ArgumentParser()
        # TODO make device_choices extensible by looking in a directory at runtime
        # say by looking for modules in the eieio.meter_desc package that conform fully to
        # the eieio.meter_desc.meter_abstractions abstract base class
        device_choices = ['i1pro', 'sekonic', 'cs2000']
        # type=str.lower courtesy of https://stackoverflow.com/questions/27616778/case-insensitive-argparse-choices
        self._parser.add_argument('--device', '-d', type=str.lower, choices=device_choices)
        self._parser.add_argument('--mode', '-m', type=str.lower, choices=['EMISSIVE', 'AMBIENT', 'REFLECTIVE'])
        self._parser.add_argument('--colorspace', '-c', type=str.lower, choices=['xyz', 'lab'])
        self._parser.add_argument('--base_measurement_name', '-b')
        self._parser.add_argument('--sample_make')
        self._parser.add_argument('--sample_model')
        self._parser.add_argument('--sample_description')
        self._parser.add_argument('--location')
        self._parser.add_argument('--sequence_preflight')
        self._parser.add_argument('--sequence_file', '-s')
        self._parser.add_argument('--frame_preflight')
        self._parser.add_argument('--frame_postflight')
        self._parser.add_argument('--output_dir', '-o')
        self._parser.add_argument('--create_parent_dirs', '-p', action='store_true')
        self._parser.add_argument('--output_dir_exists_ok', '-e', action='store_true')
        self._parser.add_argument('--verbose', '-v', action='store_true')
        self._args = self._parser.parse_args(arg_source)
        # check and if found set verbosity as early as possible, so parse/merge can reference it
        if self._args.verbose:
            self.verbose = self._args.verbose
        if self._args.sequence_file:
            self.sequence_file = self._args.sequence_file
            if not Path(self.sequence_file).exists():
                print(f"the specified sequence file `{self.sequence_file}' does not exist")
                print(f"the current working directory is {getcwd()}")
                raise RuntimeError(f"specified sequence file `{self.sequence_file}' does not exist")
        self._merge_all_files_defaults(self.sequence_file, 'sequence file specified on command line')
        args_as_dict = vars(self._args)
        for attr in ['location', 'sample_make', 'sample_model', 'sample_description',
                     'meter_desc', 'mode', 'colorspace', 'create_parent_dirs', 'output_dir_exists_ok',
                     'output_dir', 'sequence_preflight',
                     'frame_preflight', 'base_measurement_mode', 'frame_postflight']:
            if attr in args_as_dict:
                value = args_as_dict[attr]
                if value:
                    if self.verbose:
                        print(f"setting `{attr}' to `{value}' from command-line argument")
                    setattr(self, attr, value)
        missing_required_attributes = []
        for attr in ['meter', 'mode', 'base_measurement_name', 'sample_make', 'sample_model',
                     'sample_description', 'location', 'sequence_file']:
            if not getattr(self, attr):
                missing_required_attributes.append(attr)
                print(f"required argument `{attr}' is missing")
        if missing_required_attributes:
            raise RuntimeError("Can't determine what to do since required argument(s) "
                               f"{oxford_join(missing_required_attributes, 'and')} missing")
        if self._args.mode:
            mode_dict = {'emissive': MeasurementMode.EMISSIVE,
                         'ambient': MeasurementMode.AMBIENT,
                         'reflective': MeasurementMode.REFLECTIVE}
            self.mode = mode_dict[self._args.mode.lower()]

    def consistency_check(self):
        # TODO if the device is a sekonic, make sure it's a file:/path URL
        # really you want to pass that to an argument validation class method on Sekonic, no?
        # self._parser.mode = NAMED_MODES[self._parser.mode.lower()]
        # TODO make sure all three members of a colorimetric configuration are there
        return True, ''


if __name__ == '__main__':
    main_desc = 'measure a sequence of stimuli, gathering spectra and (optionally) colorimetry'
    instructions = Instructions(__file__, main_desc)
    print(instructions)
    consistent, issues = instructions.consistency_check()
    if not consistent:
        print('the following issues were detected in extended argument consistency checking:')
        print(issues)
