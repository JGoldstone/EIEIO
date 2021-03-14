from eieio.meter.meter_abstractions import SpectroradiometerBase, Mode

CMD_RESULT_READ_TIMEOUT = 5

def default_cs2000_tty():
    return '/dev/tty.usbmodem12345678901' if platform.system().lower() == 'darwin' else '/dev/ttyACM0'

class InvalidCmd(RuntimeError):
    def __init__(self):
        pass


class MeasurementInProgress(RuntimeError):
    def __init__(self):
        pass


class NoCompensationValues(RuntimeError):
    def __init__(self):
        pass


class ExcessiveBrightnessOrFlicker(RuntimeError):
    def __init__(self):
        pass


class InvalidParameterValue(RuntimeError):
    def __init__(self):
        pass


class NoData(RuntimeError):
    def __init__(self):
        pass


class InstrumentInternalMemoryError(RuntimeError):
    def __init__(self):
        pass


class ExcessiveAmbientTemperature(RuntimeError):
    def __init__(self):
        pass


class ExternalSyncFailure(RuntimeError):
    def __init__(self):
        pass


class ShutterOperationError(RuntimeError):
    def __init__(self):
        pass


class InternalNDFilterOperationError(RuntimeError):
    def __init__(self):
        pass


class AbnormalMeasurementAngle(RuntimeError):
    def __init__(self):
        pass


class CoolingFanFailure(RuntimeError):
    def __init__(self):
        pass


class ProgramAbnormality(RuntimeError):
    def __init__(self):
        pass


class CS2000(SpectroradiometerBase):
    def __init__(self, device_path=default_cs2000_tty()):
        self.delim = '\n'
        self.tty = None
        self.tty = open(device_path, 'r')
        try:
            immed_cmd(REMOTE_MODE_CMD, REMOTE_MODE_ON_WITHOUT_FLASH_WRITING)
        except

    def __del__(self):
        if self.tty:
            try:
                self.tty.close()
            finally:
                self.tty = None

    def read_with_timeout(self, timeout):
        # TODO implement timeout
        return self.tty.read()

    def immed_cmd(self, cmd, *args):
        cmd_and_args = [cmd].extend(args)
        encoded_cmd_and_args = ','.join(cmd_and_args).encode()
        self.tty.write(encoded_cmd_and_args)
        try:
            # TODO needs to be read with timeout
            result = self.read_with_timeout(CMD_RESULT_READ_TIMEOUT)
        except CmdResultReadTimeout as e:
            print(f"cmd `{cmd}' did not return a result within {e.duration()} seconds")
            raise e
        if result in FAILING_CS2000_ECCS.keys():
            raise FAILING_CS2000_ECCS[result](f"reading response from `{cmd}' with args `{args}'")

    def make(self):
        """Return the meter manufacturer's name"""
        return 'Konica/Minolta'

    def model(self):
        """Return the meter model name"""
        product_name, variation_code, serial_number = immed_cmd(IDENTIFICATION_DATA_READ_CMD)




    def serial_number(self):
        """Return the meter serial number"""
        raise NotImplementedError

    def firmware_version(self):
        """Return the meter firmware version"""
        raise NotImplementedError

    def sdk_version(self):
        """Return the manufacturer's meter SDK version"""
        raise NotImplementedError

    def adapter_version(self):
        """Return the meter adapter (proprietary SDK legal isolation layer) version"""
        raise NotImplementedError

    def adapter_module_version(self):
        """Return the meter adapter module (Python <-> C/C++ meter adapter) version"""
        raise NotImplementedError

    def meter_driver_version(self):
        """Return the meter driver (MeterBase concrete subclass) version"""
        raise NotImplementedError

    def measurement_modes(self):
        """Return the modes (EMISSIVE, reflective, &c) of measurement the meter provides"""
        return [Mode.EMISSIVE]

    def measurement_mode(self):
        """Return the measurement mode for which the meter is currently configured"""
        raise Mode.EMISSIVE

    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        raise NotImplementedError

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    def set_integration_mode(self, mode):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        raise NotImplementedError

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        raise NotImplementedError

    def calibration_and_calibration_expiration_time(self, mode):
        """Return the first time at which the calibration for the given mode will no longer be valid"""
        raise NotImplementedError

    def calibrate(self, wait_for_button_press):
        """calibrates for the current measurement mode"""
        raise NotImplementedError

    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode"""
        raise NotImplementedError

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
        """Return the colorimetry indicated by the current mode. Blocks until available"""
        return NotImplementedError

    def spectral_range_supported(self):
        """Return the minimum and maximum wavelengths. in nanometers, to which the meter is sensitive"""
        raise NotImplementedError

    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        raise NotImplementedError

    def bandwidth_fhwm(self):
        """Return the meter's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    def spectral_distribution(self):
        """Return the spectral distribution indicated by the current mode. Blocks until available"""
        return NotImplementedError
