# -*- coding: utf-8 -*-
"""
Concrete class implementing support for i1Pro spectroreadometers
===================

Implement support for the i1Pro2 (i1Pro Rev E)

"""

from .meter_abstractions import SpectroradiometerBase, Mode
from pkg_resources import require
require("i1ProAdapter")
import i1ProAdapter

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'I1Pro'
]

DRIVER_VERSION_MAJOR = 0
DRIVER_VERSION_MINOR = 1
DRIVER_VERSION_REVISION = 0
DRIVER_VERSION_BUILD = ''
DRIVER_VERSION_SUFFIX = 'pre-alpha'


class I1Pro(SpectroradiometerBase):
    def __init__(self):
        i1ProAdapter.attach()
        i1ProAdapter.openConnection(False)
        self._make, self._model, self._serial_number = i1ProAdapter.meterID()
        self._sdk_version = i1ProAdapter.sdkVersion()
        self._adapter_version = i1ProAdapter.moduleVersion()

    def __del__(self):
        i1ProAdapter.closeConnection(False)
        i1ProAdapter.detach()

    def make(self):
        """Return the meter manufacturer's name"""
        return self._make

    def model(self):
        """Return the meter model name"""
        return self._model

    def serial_number(self):
        """Return the meter serial number"""
        return self._serial_number

    def firmware_version(self):
        """Return the meter firmware version"""
        raise NotImplementedError

    def sdk_version(self):
        """Return the manufacturer's meter SDK version"""
        return self._sdk_version

    def adapter_version(self):
        """Return the meter adapter (Python <-> C/C++ SDK) version"""
        return self._adapter_version

    def driver_version(self):
        """Return the meter driver (MeterBase concrete subclass) version"""
        return f"{DRIVER_VERSION_MAJOR}.{DRIVER_VERSION_MINOR}.{DRIVER_VERSION_REVISION}.{DRIVER_VERSION_BUILD}.{DRIVER_VERSION_SUFFIX}"

    def measurement_modes(self):
        """Return the modes (emissive, reflective, &c) of measurement the meter provides"""
        # TODO should implememt measurementModes() in i1ProAdapterModule and return value of that
        return [Mode.reflective, Mode.emissive]

    def active_measurement_mode(self):
        """Return the measurement mode for which the meter is currently configured"""
        # TODO should implememt measurementModes() in i1ProAdapterModule and return value of that
        raise NotImplementedError

    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        if mode == Mode.reflective:
            i1ProAdapter.setMeasurementMode('reflective')
        elif mode == Mode.emissive:
            i1ProAdapter.setMeasurementMode('emissive')
        else:
            raise RuntimeError(f"unknown measurement mode `{mode}'")

    def last_calibration_time(self, mode):
        """Return the time the meter was lasts calibrated for the given mode"""
        raise NotImplementedError

    def calibration_expiration_time(self, mode):
        """Return the first time at which the calibration for the given mode will no longer be valid"""
        raise NotImplementedError

    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode"""
        i1ProAdapter.trigger()

    def colorspaces(self):
        """Returns the set of colorspaces in which the device can provide colorimetry"""
        raise NotImplementedError

    def current_colorspace(self):
        """Returns the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    def set_current_colorspace(self):
        """Sets the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    def read_colorimetry(self):
        """Return the colorimetry indicated by the current mode. Blocks until available"""
        triplet = i1ProAdapter.measuredColorimetry()
        # TODO find the Python idiom for this
        return triplet[0], triplet[1], triplet[2]

    def spectral_range_supported(self):
        """Return the minimum and maximum wavelengths. in nanometers, to which the meter is sensitive"""
        spectral_range = i1ProAdapter.spectralRange()
        return spectral_range[0], spectral_range[1]

    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        return i1ProAdapter.measuredSpectrum()

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        raise NotImplementedError

    def bandwidth_fhwm(self):
        """Return the meter's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    def read_spectral_distribution(self):
        """Return the spectral distribution indicated by the current mode. Blocks until available"""
        return NotImplementedError
