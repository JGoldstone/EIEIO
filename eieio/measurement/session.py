# -*- coding: utf-8 -*-
"""
Measurement session structure and I/O
================================

Defines the :class:`spectral_measurement.session.MeasurementSession` class handling directories full of
*IES TM-27-14* spectral data XML files.

"""

import os
from datetime import datetime
from pathlib import Path

from colour.io.tm2714 import SpectralDistribution_IESTM2714
from eieio.measurement.colorimetry import Colorimetry_IESTM2714

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'MeasurementSession'
]

SPECTRAL_SUFFIX = '.spdx'
COLORIMETRIC_SUFFIX = '.colx'


class MeasurementSession(object):
    """
    Manages a collection of related spectral and/or colorimetric measurements

    Attributes
    sds : dict
        colour.colorimetry.spectrum.SpectralDistribution objects, keyed by filename
    tsc_colorspace : str
        name of tristimulus color space.
    tscs : dict
        tristimulus colorimetry measurements, keyed by filename
    """

    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

    @staticmethod
    def timestamp():
        return datetime.now().strftime(MeasurementSession.TIMESTAMP_FORMAT)

    def __init__(self, measurement_dir):
        """
        Constructor for MeasurementSession object, holding sds and tscs and tracking which ones need writing
        """
        self._sds = {}
        self._dirty_sds_keys = set()
        self._tscs = {}
        self._dirty_tscs_keys = set()
        self.measurement_dir = measurement_dir

    def load(self):
        for _, _, files in os.walk(self.measurement_dir):
            files.sort()
            for file in files:
                if Path(file).suffix == SPECTRAL_SUFFIX:
                    measurement_path = str(Path(self.measurement_dir, file))
                    sd = SpectralDistribution_IESTM2714(measurement_path)
                    sd.read()
                    self.add_spectral_measurement(sd)
                elif Path(file).suffix == COLORIMETRIC_SUFFIX:
                    tcm = Colorimetry_IESTM2714(file)
                    self.add_tristimulus_colorimetry_measurement(tcm)

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
            print(f"writing tristimulus colorimetry to {tsc.path}")
            tsc.write()
        self._dirty_tscs_keys = set()

    def add_timestamped_measurement(self, measurement, dict_, key_set):
        addition_timestamp = self.timestamp()
        # There shouldn't already be a directory but just in case, remove any before
        # setting up this spectral_measurement for later saving to the spectral_measurement session_dir.
        measurement.path = str(Path(self.measurement_dir, Path(measurement.path).name))
        dict_[measurement.path] = measurement
        key_set.add(measurement.path)

    def add_spectral_measurement(self, measurement):
        self.add_timestamped_measurement(measurement, self._sds, self._dirty_sds_keys)

    def add_tristimulus_colorimetry_measurement(self, measurement):

        self.add_timestamped_measurement(measurement, self._tscs, self._dirty_tscs_keys)

    def contains_unsaved_measurements(self):
        return len(self._dirty_sds_keys) > 0 or len(self._dirty_tscs_keys) > 0

    @property
    def sds(self):
        return self._sds

    @property
    def tscs(self):
        return self._tscs
