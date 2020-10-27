# -*- coding: utf-8 -*-
"""
Measurement session structure and I/O
================================

Defines the :class:`measurement.session.MeasurementSession` class handling directories full of
*IES TM-27-14* spectral data XML files and a supplementary README.md file
documenting the measurement session's motiviation and procedure.

"""

from datetime import datetime
from pathlib import Path

import toml
import os

from colour import SpectralDistribution_IESTM2714
from measurement.tristim_colorimetry import TristimulusColorimetryMeasurement

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'MeasurementSession'
]

README_FILENAME = 'README.md'

SPECTRAL_SUFFIX = '.spdx'
COLORIMETRIC_SUFFIX = '.colx'


class MeasurementSession(object):
    """
    Manages a collection of related spectral and/or colorimetric measurements

    Sessions are not intended to be saved; they might be useful as part of a database
    loader someday, but for now they are handy ways to group measurements for presentation
    to Dash apps, or whatever.

    Attributes
    sds : dict
        colour.colorimetry.spectrum.SpectralDistribution objects, keyed by filename
    tsc_colorspace : str
        name of tristimulus color space.
    tscs : dict
        tristumulus colorimetry measurements, keyed by filename

    """

    EIEIO_CONFIG = "eieio.toml"
    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

    @staticmethod
    def timestamp():
        return datetime.now().strftime(MeasurementSession.TIMESTAMP_FORMAT)

    @staticmethod
    def load_eieio_defaults():
        default = {'measurements': {'base_dir_path': '/var/tmp'}}
        config_path = Path(MeasurementSession.EIEIO_CONFIG).resolve()
        if not config_path.exists():
            return default
        try:
            try:
                result = toml.load(str(config_path))
                return result
            except toml.decoder.TomlDecodeError as e:
                print(f"error decoding EIEIO config file: {e}")
                return default
        except FileNotFoundError:
            return default

    @staticmethod
    def check_path_is_writable_dir(path, desc):
        p = Path(path)
        if p.exists():
            if not p.is_dir():
                raise FileExistsError(f"measurement base dir `{path}' exists, but is not a directory")
            else:
                if not os.access(path, os.W_OK):
                    raise ProcessLookupError(f"cannot write to {desc} `{path}'")
        else:
            raise FileNotFoundError(f"{desc} `{path}' not found")

    @staticmethod
    def default_path_component_from_eieio(component, default_default, eieio_attribute):
        if component:
            return component
        try:
            eieio_defaults = MeasurementSession.load_eieio_defaults()
            split_attrs = eieio_attribute.split('.')
            node = eieio_defaults
            for i, attr in enumerate(split_attrs):
                if attr in node:
                    if i == len(split_attrs) - 1:
                        return node[attr]  # leaf, pass back value
                    else:
                        node = node[attr]  # go deeper
                else:
                    raise ValueError(f"could not find value of eieio attribute '{eieio_attribute}'")
        except ValueError:
            return default_default

    @staticmethod
    def resolve_measurement_dir(base_dir_path=None, dir_name=None):
        base_dir_path = MeasurementSession.default_path_component_from_eieio(base_dir_path, '/var/tmp',
                                                                             'measurements.base_dir_path')
        MeasurementSession.check_path_is_writable_dir(base_dir_path, "measurement base dir")
        dir_name = MeasurementSession.default_path_component_from_eieio(dir_name,
                                                                        MeasurementSession.timestamp(),
                                                                        'measurements.dir_name')
        return Path(base_dir_path) / dir_name

    @staticmethod
    def prepare_measurement_dir(base_dir_path, dir_name):
        measurement_dir = MeasurementSession.resolve_measurement_dir(base_dir_path, dir_name)
        if not measurement_dir.exists():
            measurement_dir.mkdir()
        return measurement_dir

    def __init__(self, base_dir_path=None, dir_name=None):
        """
        Construcutor for MeasurementSession object, holding sds and tscs and tracking which need writing

        Determines the directory where measurements will be placed by examining its arguments and by
        defaulting, if needed, from the measurement.base_dir_path and measurement.dir_name properties
        of an eieio.toml file, if found. If all else fails, the measurement base directory defaults to
        /var/tmp, and the directory name defaults to a timestamp.
        """
        self._sds = {}
        self._dirty_sds_keys = set()
        self._tscs = {}
        self._dirty_tscs_keys = set()
        self.measurement_dir = MeasurementSession.prepare_measurement_dir(base_dir_path, dir_name)
        for _, _, files in os.walk(self.measurement_dir):
            for file in files:
                if Path(file).suffix == SPECTRAL_SUFFIX:
                    self.add_spectral_measurement(SpectralDistribution_IESTM2714(file))
                elif Path(file).suffix == COLORIMETRIC_SUFFIX:
                    self.add_tristimulus_colorimetry_measurement(TristimulusColorimetryMeasurement(file))

    def save(self):
        for key in self._dirty_sds_keys:
            sd = self._sds[key]
            if not sd:
                raise RuntimeError(f"could not find spectral distribution with path {key}")
            print(f"writing spectral distribution to {sd.path}")
            sd.write()
        self._dirty_sds_keys = set()
        for key in self._dirty_tscs_keys:
            tsc = self._tscs[key]
            if not tsc:
                raise RuntimeError(f"could not find tristimulus colorimetry with path {key}")
            print(f"writing tristimulus colorimetry to {sd.path}")
            tsc.write()
        self._dirty_tscs_keys = set()

    def add_timestamped_measurement(self, measurement, dict_, key_set):
        addition_timestamp = self.timestamp()
        measurement.path = str(Path(self.measurement_dir, addition_timestamp))
        dict_[addition_timestamp] = measurement
        key_set.add(addition_timestamp)

    def add_spectral_measurement(self, measurement):
        self.add_timestamped_measurement(measurement, self._sds, self._dirty_sds_keys)

    def existing_tsc_colorspace(self):
        assert len(self._tscs) > 0
        for value in self._tscs.values():
            return value.colorspace

    def add_tristimulus_colorimetry_measurement(self, measurement):
        if self._tscs:
            existing_cs = self.existing_tsc_colorspace()
            if measurement.colorspace != existing_cs:
                raise RuntimeError(
                    f"measurement session cannot add tristimulus colorimetry in space {measurement.colorspace} because session already has data in {existing_cs}")
        self.add_timestamped_measurement(measurement, self._tscs, self._dirty_tscs_keys)

    def contains_unsaved_measurements(self):
        return len(self._dirty_sds_keys) > 0 or len(self._dirty_tscs_keys)  > 0
