# -*- coding: utf-8 -*-
"""
Abstract base classes for metering devices used in colour science work
===================

Defines an abstract generic meter base class and then a spectroradiometer subclass (but still abstract)

"""

from enum import Enum

from abc import ABC, abstractmethod

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'IntegrationMode', 'Observer', 'Mode', 'Quantity', 'State',
    'MeterError',
    'ColorimeterBase', 'SpectroradiometerBase'
]

# TODO See if there is a way to generate this automatically from the protobuf file in ../../services/protobufs


class IntegrationMode(Enum):
    UNKNOWN = 0
    ADAPTIVE = 1
    MULTI_SAMPLE_ADAPTIVE = 2
    FAST = 3  # so far only seen on Konica/Minolta CS2000[A]
    MULTI_SAMPLE_FAST = 4  # same
    FIXED = 4


class Observer(Enum):
    UNKNOWN = 0
    TWO_DEGREE_1931 = 1
    TEN_DEGREE_1964 = 2


class Mode(Enum):
    UNKNOWN = 0
    EMISSIVE = 1
    AMBIENT = 2
    REFLECTIVE = 3
    TRANSMISSIVE = 4


class Quantity(Enum):
    UNKNOWN = 0
    RADIANCE = 1
    SPECTRAL_RADIANCE = 2
    IRRADIANCE = 3
    SPECTRAL_IRRADIANCE = 4
    RADIANT_INTENSITY = 5
    SPECTRAL_RADIANT_INTENSITY = 6
    RADIANT_FLUX = 7
    SPECTRAL_RADIANT_FLUX = 8
    LUMINANCE = 9
    ILLUMINANCE = 10


class State(Enum):
    UNATTACHED = 0
    UNCALIBRATED = 1
    CALIBRATION_IN_PROGRESS = 2
    CALIBRATED = 3
    MEASUREMENT_IN_PROGRESS = 4
    MEASUREMENT_COMPLETE = 5
    READOUT_IN_PROGRESS = 6


class MeterError(Exception):
    def __init__(self, what):
        self._what = None
        self.what = what

    @property
    def what(self):
        return self._what

    @what.setter
    def what(self, value):
        self._what = value


class ColorimeterBase(ABC):
    @abstractmethod
    def make(self):
        """Return the meter manufacturer's name"""
        raise NotImplementedError

    @abstractmethod
    def model(self):
        """Return the meter model name"""
        raise NotImplementedError

    @abstractmethod
    def serial_number(self):
        """Return the meter serial number"""
        raise NotImplementedError

    @abstractmethod
    def firmware_version(self):
        """Return the meter firmware version"""
        raise NotImplementedError

    @abstractmethod
    def sdk_version(self):
        """Return the manufacturer's meter SDK version"""
        raise NotImplementedError

    @abstractmethod
    def adapter_version(self):
        """Return the meter adapter (proprietary SDK legal isolation layer) version"""
        raise NotImplementedError

    @abstractmethod
    def adapter_module_version(self):
        """Return the meter adapter module (Python <-> C/C++ meter adapter) version"""
        raise NotImplementedError

    @abstractmethod
    def meter_driver_version(self):
        """Return the meter driver (MeterBase concrete subclass) version"""
        raise NotImplementedError

    @abstractmethod
    def measurement_modes(self):
        """Return the modes (EMISSIVE, reflective, &c) of measurement the meter provides"""
        raise NotImplementedError

    @abstractmethod
    def measurement_mode(self):
        """Return the measurement mode for which the meter is currently configured"""
        raise NotImplementedError

    @abstractmethod
    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        raise NotImplementedError

    @abstractmethod
    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    @abstractmethod
    def set_integration_mode(self, mode, integration_time):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    @abstractmethod
    def integration_time_range(self):
        """Return the minimum and maximum integration time supported, in seconds"""
        raise NotImplementedError

    @abstractmethod
    def measurement_angles(self):
        """Returns the set of supported discrete measurement angles, in degrees"""

    @abstractmethod
    def measurement_angle(self):
        """Returns the currently-set measurement angle, in degrees"""

    @abstractmethod
    def set_measurement_angle(self, angle):
        """Sets the measurement angle, in degrees"""

    @abstractmethod
    def calibration_and_calibration_expiration_time(self, mode):
        """Return the first time at which the calibration for the given mode will no longer be valid"""
        raise NotImplementedError

    @abstractmethod
    def calibrate(self, wait_for_button_press=False):
        """calibrates for the current measurement mode"""
        raise NotImplementedError

    @abstractmethod
    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode
        Raises
        ------
        MeterError

        Returns
        -------
        True if measurement was successfully triggered
        """
        raise NotImplementedError

    @abstractmethod
    def colorspaces(self):
        """Returns the set of colorspaces in which the device can provide colorimetry"""
        raise NotImplementedError

    @abstractmethod
    def colorspace(self):
        """Returns the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    @abstractmethod
    def set_colorspace(self, colorspace):
        """Sets the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    @abstractmethod
    def illuminants(self):
        """Returns the set of illuminants which the device can use in converting spectroradiometry to colorimetry"""
        raise NotImplementedError

    @abstractmethod
    def illuminant(self):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    @abstractmethod
    def set_illuminant(self, illuminant):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    @abstractmethod
    def colorimetry(self):
        """Return the colorimetry indicated by the current mode. Blocks until available"""
        return NotImplementedError


class SpectroradiometerBase(ColorimeterBase):
    @abstractmethod
    def spectral_range_supported(self):
        """Return the minimum and maximum wavelengths. in nanometers, to which the meter is sensitive"""
        raise NotImplementedError

    @abstractmethod
    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        raise NotImplementedError

    @abstractmethod
    def bandwidth_fhwm(self):
        """Return the meter's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    @abstractmethod
    def spectral_distribution(self):
        """Return the spectral distribution indicated by the current mode. Blocks until available
        Raises
        ------
        MeterError

        Returns
        -------
        power_by_wavelength : sequence
            a sequence of floating-point numbers read by the instrument
        """
        return NotImplementedError
