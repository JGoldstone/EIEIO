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

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'MeasurementSession'
]

EIEIO_CONFIG = "eieio.toml"
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

    measurement_dir = None

    @staticmethod
    def timestamp():
        return datetime.now().strftime("%Y-%m-%dT%h:%M:%S")

    @staticmethod
    def load_eieio_defaults():
        if not Path(EIEIO_CONFIG):
            return {'base_dir_path': '/var/tmp/'}
        return toml.load(EIEIO_CONFIG)

    @staticmethod
    def resolve_measurement_dir(base_dir_path=None, meas_dir_name=None):
        if not base_dir_path:
            eieio_defaults = MeasurementSession.load_eieio_defaults()
            base_dir_path = Path(eieio_defaults['base_dir_path'])
        else:
            base_dir_path = Path(base_dir_path)
        if base_dir_path.exists():
            if not base_dir_path.is_dir():
                raise FileExistsError(f"measurement base dir {base_dir_path} exists, but is not a directory")
            else:
                # TODO check if dir is writable
                pass
        else:
            raise FileNotFoundError(f"measurement base dir {base_dir_path} not found")
        if not meas_dir_name:
            meas_dir_name = MeasurementSession.timestamp()
        meas_dir_path = Path(base_dir_path,  meas_dir_name)
        if not meas_dir_path.exists():
            meas_dir_path.mkdir()
        return meas_dir_path

    def __init__(self, base_dir_path=None, meas_dir_name=None):
        """
        Construcutor for MeasurementSession object, holding sds and tscs and tracking which need writing
        """
        self._sds = {}
        self._dirty_sds_keys = set()
        self._tscs = {}
        self._dirty_tscs_keys = set()
        if not MeasurementSession.measurement_dir:
            resolved_dir = MeasurementSession.resolve_measurement_dir(base_dir_path, meas_dir_name)
            MeasurementSession.measurement_dir = resolved_dir
        for _, _, files in os.walk(MeasurementSession.measurement_dir):
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
            sd.write()
        for key in self._dirty_tscs_keys:
            tsc = self._tscs[key]
            if not tsc:
                raise RuntimeError(f"could not find tristimulus colorimetry with path {key}")
            tsc.write()

    def add_spectral_measurement(self, measurement):
        if not measurement.path:
            measurement.path = str(Path(MeasurementSession.measurement_dir, self.timestamp()))
        self._sds += measurement
        self._dirty_sds_keys += [measurement.path]

    def add_tristimulus_colorimetry_measurement(self, measurement):
        if not measurement.path:
            measurement.path = str(Path(MeasurementSession.measurement_dir, self.timestamp()))
        if self._tscs:
            for value in self._tscs.values():  # get the first, that suffices
                existing_colorspace = value.colorspace
            if measurement.colorspace != existing_colorspace:
                raise RuntimeError(f"measurement session cannot add tristimulus colorimetry in space {colorspace} because session already has data in {self._tsc_colorspace}")
        self._tscs += [measurement]
