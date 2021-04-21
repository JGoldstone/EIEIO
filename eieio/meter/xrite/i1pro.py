# -*- coding: utf-8 -*-
"""
Concrete class implementing support for i1Pro spectroreadometers
===================

Implement support for the i1Pro2 (i1Pro Rev E)

"""

from eieio.meter.meter_abstractions import SpectroradiometerBase, Observer  # , Mode
from services.metering.metering_pb2 import MeasurementMode, IntegrationMode, ColorSpace, Illuminant
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

I1PRO_TO_METERING_COLOR_SPACE_MAP = {
    'CIELab': ColorSpace.CIE_LAB,
    'CIELCh': ColorSpace.CIE_LCh,
    'CIELuv': ColorSpace.CIE_Luv,
    'CIELChuv': ColorSpace.CIE_LChuv,
    'CIEuvY1960': ColorSpace.CIE_uv_1960,
    'CIEuvY1976': ColorSpace.CIE_uv_1976,
    'CIEXYZ': ColorSpace.CIE_XYZ,
    'CIExyY': ColorSpace.CIE_xyY
}

I1PRO_TO_METERING_ILLUMINANT_MAP = {
    'A': Illuminant.A,
    'B': Illuminant.B,
    'C': Illuminant.C,
    'D50': Illuminant.D50,
    'D55': Illuminant.D55,
    'D65': Illuminant.D65,
    'D75': Illuminant.D75,
    'F2': Illuminant.F2,
    'F7': Illuminant.F7,
    'F11': Illuminant.F11,
    'Emission': Illuminant.EMISSION
}


class I1Pro(SpectroradiometerBase):
    def __init__(self):
        # i1ProAdapter.attach()
        i1ProAdapter.openConnection(False)
        self._make, self._model, self._serial_number = i1ProAdapter.meterID()
        self._sdk_version = i1ProAdapter.sdkVersion()
        self._adapter_module_version = i1ProAdapter.adapterModuleVersion()

    def __del__(self):
        i1ProAdapter.closeConnection(False)
        i1ProAdapter.detach()

    def make(self):
        """Return the meter_desc manufacturer's name"""
        return self._make

    def model(self):
        """Return the meter_desc model name"""
        return self._model

    def serial_number(self):
        """Return the meter_desc serial number"""
        return self._serial_number

    def firmware_version(self):
        """Return the meter_desc firmware version"""
        return None

    def sdk_version(self):
        """Return the manufacturer's meter_desc SDK version"""
        return self._sdk_version

    def adapter_version(self):
        """Return the meter_desc adapter (proprietary SDK legal isolation layer) version"""
        return self._sdk_version

    def adapter_module_version(self):
        """Return the meter_desc adapter module (Python <-> C/C++ meter_desc adapter) version"""
        return self._adapter_module_version

    def meter_driver_version(self):
        """Return the meter_desc driver (MeterBase concrete subclass) version"""
        result = f"{DRIVER_VERSION_MAJOR}.{DRIVER_VERSION_MINOR}.{DRIVER_VERSION_REVISION}"
        result += ".{DRIVER_VERSION_BUILD}.{DRIVER_VERSION_SUFFIX}"
        return result

    def measurement_modes(self):
        """Return the modes (EMISSIVE, REFLECTIVE, &c) of measurement the meter_desc provides"""
        retrieved_modes = i1ProAdapter.measurementModes()
        modes = []
        for mode in retrieved_modes:
            try:
                matched_mode = MeasurementMode.Value(mode.upper())
                modes.append(matched_mode)
            except KeyError:
                pass
        return modes

    def measurement_mode(self):
        """Return the measurement mode for which the meter_desc is currently configured"""
        retrieved_mode = i1ProAdapter.measurementMode()
        try:
            return MeasurementMode.Value(retrieved_mode[0].upper())
        except KeyError:
            return MeasurementMode.UNKNOWN

    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        try:
            i1ProAdapter.setMeasurementMode(MeasurementMode.Name(mode).lower())
        except IOError:
            raise RuntimeError((f"cannot set measurement mode to unknown mode "
                                f"`{MeasurementMode.Name(mode)}"))

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        return [IntegrationMode.ADAPTIVE]

    def integration_mode(self):
        """Return the integration mode for which the meter is currently configured"""
        return IntegrationMode.ADAPTIVE

    def set_integration_mode(self, mode, integration_time):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        if mode is not IntegrationMode.ADAPTIVE:
            raise NotImplementedError("""The i1Pro driver only supports adaptive integration at this time. 
File a PR if you need static integration time.""")

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported, in seconds"""
        raise NotImplementedError

    def measurement_angles(self):
        """Returns the set of supported discrete measurement angles, in degrees"""
        return [2.0]

    def measurement_angle(self):
        """Returns the currently-set measurement angle, in degrees"""
        return 2.0

    def set_measurement_angle(self, angle):
        """Sets the measurement angle, in degrees"""
        raise NotImplementedError

    def calibration_times(self):
        since, until = i1ProAdapter.getCalibrationTimes()
        # since and until are actually strings at this point; handling weirdness is easier in Python than straight C
        now = datetime.now()
        calibration_time = now - (timedelta(hours=8) if since == '-1' else timedelta(seconds=int(since)))
        expiration_time = now if until == '-1' else now + timedelta(seconds=int(until))
        return calibration_time, expiration_time

    def promptForCalibrationPositioning(self, prompt=None):
        """Prompt the user to set the meter up for calibration (e.g. put on calibratino tile)"""
        print('Position i1Pro on calibration tile, and press RETURN: ', flush=True, end='')
        _ = input()
        print(flush=True)

    def calibrate(self, wait_for_button_press=True):
        return i1ProAdapter.calibrate(wait_for_button_press)

    def promptForMeasurementPositioning(self, prompt=None):
        """Prompt the user to set the meter up for calibration (e.g. put on calibratino tile)"""
        print('Position i1Pro in relation to target, and press RETURN: ', flush=True, end='')
        _ = input()
        print(flush=True)

    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode

        Returns
        -------
        float indicating probable number of seconds required for integration time (0 for i1Pro series)"""
        i1ProAdapter.trigger()
        return 0

    def color_spaces(self):
        """Returns the set of color spaces in which the device can provide colorimetry"""
        return list(I1PRO_TO_METERING_COLOR_SPACE_MAP.values())

    def color_space(self):
        """Returns the colorspace in which colorimetric data will be returned"""
        cs = i1ProAdapter.colorspace()
        return I1PRO_TO_METERING_COLOR_SPACE_MAP[cs]

    def set_color_space(self, color_space):
        """Sets the color space in which colorimetric data will be returned"""
        # https://stackoverflow.com/questions/2568673/inverse-dictionary-lookup-in-python
        cs = [k for k, v in I1PRO_TO_METERING_COLOR_SPACE_MAP.items() if v == color_space][0]
        print(f"cs is `{cs}'", flush=True)
        i1ProAdapter.setColorspace(cs)
        print('back from i1ProAdapter.setColorspace')

    def illuminants(self):
        """Returns the set of illuminants which the device can use in converting spectroradiometry to colorimetry"""
        return list(I1PRO_TO_METERING_ILLUMINANT_MAP.values())

    def illuminant(self):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        il = i1ProAdapter.illuminant()
        return I1PRO_TO_METERING_ILLUMINANT_MAP[il]

    def set_illuminant(self, illuminant):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        il = [k for k, v in I1PRO_TO_METERING_ILLUMINANT_MAP.items() if v == illuminant][0]
        print(f"il is `{il}'", flush=True)
        i1ProAdapter.setIlluminant(il)
        print('back from i1ProAdapter.setIlluminant')

    def colorimetry(self):
        """Return tuplie containing the colorimetry indicated by the current mode. Blocks until available"""
        return i1ProAdapter.measuredColorimetry()

    # rename this to spectral_range
    def spectral_range_supported(self):
        """Return tuple containing min and max wavelengths. in nanometers, to which the meter_desc is sensitive"""
        return i1ProAdapter.spectralRange()

    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        return i1ProAdapter.spectralResolution()

    def bandwidth_fhwm(self):
        """Return the meter_desc's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    def spectral_distribution(self):
        """Return tuple containing the spectral distribution indicated by the current mode. Blocks until available"""
        print('at debug point')
        return i1ProAdapter.measuredSpectrum()
