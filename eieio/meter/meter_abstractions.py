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
    'IntegrationMode', 'Observer', 'Mode',
    'ColorimeterBase', 'SpectroradiometerBase'
]


class IntegrationMode(Enum):
    unknown_integration_type = 0
    adaptive_integration = 1
    fixed_integration = 2


class Observer(Enum):
    unknown_observer = 0
    two_degree = 1
    ten_degree = 2


class Mode(Enum):
    unknown_mode = 0
    emissive = 1
    ambient = 2
    reflective = 3


class Quantity(Enum):
    unknown_quantity = 0
    radiance = 1


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
        """Return the modes (emissive, reflective, &c) of measurement the meter provides"""
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
    def set_integration_mode(self, mode):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    @abstractmethod
    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        raise NotImplementedError

    @abstractmethod
    def calibration_and_calibration_expiration_time(self, mode):
        """Return the first time at which the calibration for the given mode will no longer be valid"""
        raise NotImplementedError

    @abstractmethod
    def calibrate(self, wait_for_button_press):
        """calibrates for the current measurement mode"""
        raise NotImplementedError

    @abstractmethod
    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode"""
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
        """Return the spectral distribution indicated by the current mode. Blocks until available"""
        return NotImplementedError
