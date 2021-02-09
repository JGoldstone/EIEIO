# -*- coding: utf-8 -*-
"""
Concrete class implementing support for i1Pro spectroreadometers
===================

Implement support for the i1Pro2 (i1Pro Rev E)

"""

from meter.meter_abstractions import SpectroradiometerBase, IntegrationMode, Observer, Mode
from datetime import datetime, timedelta
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
        self._adapter_module_version = i1ProAdapter.adapterModuleVersion()

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
        return None

    def sdk_version(self):
        """Return the manufacturer's meter SDK version"""
        return self._sdk_version

    def adapter_version(self):
        """Return the meter adapter (proprietary SDK legal isolation layer) version"""
        return self._sdk_version

    def adapter_module_version(self):
        """Return the meter adapter module (Python <-> C/C++ meter adapter) version"""
        return self._adapter_module_version

    def meter_driver_version(self):
        """Return the meter driver (MeterBase concrete subclass) version"""
        return f"{DRIVER_VERSION_MAJOR}.{DRIVER_VERSION_MINOR}.{DRIVER_VERSION_REVISION}.{DRIVER_VERSION_BUILD}.{DRIVER_VERSION_SUFFIX}"

    def measurement_modes(self):
        """Return the modes (emissive, reflective, &c) of measurement the meter provides"""
        retrieved_modes = i1ProAdapter.measurementModes()
        modes = []
        for mode in retrieved_modes:
            try:
                _ = Mode[mode]
                modes += mode
            except KeyError:
                pass
        return modes

    def measurement_mode(self):
        """Return the measurement mode for which the meter is currently configured"""
        retrieved_mode = i1ProAdapter.measurementMode()
        try:
            return Mode[retrieved_mode]
        except KeyError:
            return Mode.unknown_mode

    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        if mode == Mode.reflective:
            i1ProAdapter.setMeasurementMode('reflective')
        elif mode == Mode.ambient:
            i1ProAdapter.setMeasurementMode('ambient')
        elif mode == Mode.emissive:
            i1ProAdapter.setMeasurementMode('emissive')
        else:
            raise RuntimeError(f"unknown measurement mode `{mode}'")

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        return [IntegrationMode.adaptive_integration]

    def set_integration_mode(self, mode):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        if mode is not IntegrationMode.adaptive_integration:
            raise NotImplementedError("""The i1Pro driver only supports adaptive integration at this time. 
File a PR if you need static integration time.""")

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        raise NotImplementedError

    def calibrate(self, wait_for_button_press):
        return i1ProAdapter.calibrate(wait_for_button_press)

    def calibration_and_calibration_expiration_time(self, mode):
        since, until = i1ProAdapter.getCalibrationTimes()
        now = datetime.now()
        return now - timedelta(seconds=since), now + timedelta(seconds=until)

    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode"""
        i1ProAdapter.trigger()

    def colorspaces(self):
        """Returns the set of colorspaces in which the device can provide colorimetry"""
        raise NotImplementedError

    def colorspace(self):
        """Returns the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    def set_colorspace(self, colorspace):
        """Sets the colorspace in which colorimetric data will be returned"""
        raise NotImplementedError

    def illuminants(self):
        """Returns the set of illuminants which the device can use in converting spectroradiometry to colorimetry"""
        raise NotImplementedError

    def illuminant(self):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    def set_illuminant(self, illuminant):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    def colorimetry(self):
        """Return tuplie containing the colorimetry indicated by the current mode. Blocks until available"""
        return i1ProAdapter.measuredColorimetry()

    # renname this to spectral_range
    def spectral_range_supported(self):
        """Return tuple containing minimum and maximum wavelengths. in nanometers, to which the meter is sensitive"""
        return i1ProAdapter.spectralRange()

    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        return i1ProAdapter.spectralResolution()

    def bandwidth_fhwm(self):
        """Return the meter's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    def spectral_distribution(self):
        """Return tuple containing the spectral distribution indicated by the current mode. Blocks until available"""
        return i1ProAdapter.measuredSpectrum()
