import asyncio
import platform
from enum import Enum

from eieio.meter.meter_abstractions import MeterError, Mode, IntegrationMode, SpectroradiometerBase

DRIVER_VERSION = '0.0.1b'
CMD_RESULT_READ_TIMEOUT = 5

OK00 = 'OK00'
ER00 = 'ER00'
ER02 = 'ER02'
ER05 = 'ER05'
ER10 = 'ER10'
ER17 = 'ER17'
ER20 = 'ER20'
ER30 = 'ER30'
ER32 = 'ER32'
ER34 = 'ER34'
ER51 = 'ER51'
ER52 = 'ER52'
ER71 = 'ER71'
ER81 = 'ER81'
ER82 = 'ER82'
ER83 = 'ER83'
ER84 = 'ER84'
ER99 = 'ER99'


class InvalidCmd(MeterError):
    def __init__(self, what):
        super(InvalidCmd, self).__init__(what)


class MeasurementInProgress(MeterError):
    def __init__(self, what):
        super(MeasurementInProgress, self).__init__(what)


class NoCompensationValues(MeterError):
    def __init__(self, what):
        super(NoCompensationValues, self).__init__(what)


class ExcessiveBrightnessOrFlicker(MeterError):
    def __init__(self, what):
        super(ExcessiveBrightnessOrFlicker, self).__init__(what)


class InvalidParameterValue(MeterError):
    def __init__(self, what):
        super(InvalidParameterValue, self).__init__(what)


class NoData(MeterError):
    def __init__(self, what):
        super(NoData, self).__init__(what)


class InstrumentInternalMemoryError(MeterError):
    def __init__(self, what):
        super(InstrumentInternalMemoryError, self).__init__(what)


class ExcessiveAmbientTemperature(MeterError):
    def __init__(self, what):
        super(ExcessiveAmbientTemperature, self).__init__(what)


class ExternalSyncFailure(MeterError):
    def __init__(self, what):
        super(ExternalSyncFailure, self).__init__(what)


class ShutterOperationError(MeterError):
    def __init__(self, what):
        super(ShutterOperationError, self).__init__(what)


class InternalNDFilterOperationError(MeterError):
    def __init__(self, what):
        super(InternalNDFilterOperationError, self).__init__(what)


class AbnormalMeasurementAngle(MeterError):
    def __init__(self, what):
        super(AbnormalMeasurementAngle, self).__init__(what)


class CoolingFanFailure(MeterError):
    def __init__(self, what):
        super(CoolingFanFailure, self).__init__(what)


class ProgramAbnormality(MeterError):
    def __init__(self, what):
        super(ProgramAbnormality, self).__init__(what)


class ReadTimeout(MeterError):
    def __init__(self, timeout):
        what = f"{timeout}-second read timeout exceeded"
        super(ReadTimeout, self).__init__(what)
        self._timeout = None

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value


class WriteFailure(MeterError):
    def __init__(self):
        what = f"failure writing to device"
        super(WriteFailure, self).__init__(what)


class UnexpectedResponse(MeterError):
    def __init__(self, what):
        super(UnexpectedResponse, self).__init__(what)


class UnexpectedCmdResponse(MeterError):
    def __init__(self, expected, actual, cmd, *args):
        sent = f"{cmd} command with args {args}" if args else f"{cmd} command"
        what = f"sent {sent}, expected {expected}, received {actual}"
        super(UnexpectedCmdResponse, self).__init__(what)


class RemoteMode(Enum):
    OFF = 0
    ON_WRITING_FROM = 1  # FROM means Flash Read Only Memory and you can wear it out
    ON_NOT_WRITING_FROM = 2


class SpeedMode(Enum):
    NORMAL = 0
    FAST = 1
    MULTI_INTEGRATION_NORMAL = 2
    MANUAL = 3
    MULTI_INTEGRATION_FAST = 4


class InternalNDFilterMode(Enum):
    OFF = 0
    ON = 1
    AUTO = 2


class MeasurementControl(Enum):
    CANCEL = 0
    START = 1


class ReadoutMode(Enum):
    CONDITIONS = 0
    SPECTRAL = 1
    COLORIMETRIC = 2


class ReadoutDataFormat(Enum):
    TEXT = 0
    BINARY = 1


class Colorspaces(Enum):
    ALL = 0
    CIE_XYZ = 1
    CIE_xyY = 2
    CIE_Luv = 3
    TEMP_TINT_Y = 4
    DOM_PUR_Y = 5
    CIE_XYZ_10 = 6
    CIE_xyY_10 = 7
    CIE_Luv_10 = 8
    TEMP_TINT_Y_10 = 9
    DOM_PUR_Y_10 = 10
    Y = 100
    Y_HUH = 101  # Huh? What's this?


def default_cs2000_tty():
    return '/dev/cu.usbmodem12345678901' if platform.system().lower() == 'darwin' else '/dev/ttyACM0'


def raise_if_not_ok(ecc, context):
    if ecc != OK00:
        raise UnexpectedResponse(f"expected response {OK00}, saw {ecc} (while {context})")


class CS2000(SpectroradiometerBase):

    def __init__(self, meter_request_and_maybe_response_path=default_cs2000_tty(),
                 meter_response_override_path=None, debug=False):
        self._debug = None
        self.debug = debug
        self.delim = '\n'
        self._tty_request_and_maybe_response = None
        if self.debug:
            print(f"opening connection to CS2000 at `{meter_request_and_maybe_response_path}'", flush=True)
        self.tty_request_and_maybe_response = open(meter_request_and_maybe_response_path, mode='r+')
        self._tty_overriding_response = None
        if meter_response_override_path:
            if self.debug:
                print(f"opening connection to response override at `{meter_response_override_path}'", flush=True)
            self.tty_overriding_response = open(meter_response_override_path, mode='r')
        if self.debug:
            print(f"sending `RTMS,{RemoteMode.ON_NOT_WRITING_FROM}' to `{meter_request_and_maybe_response_path}'",
                  flush=True)
        print(f"RTMS,{RemoteMode.ON_NOT_WRITING_FROM}", file=self.tty_request_and_maybe_response, flush=True)
        self._product_name = None
        self._product_variant = None
        self._serial_number = None
        self._colorspace = None

    def __del__(self):
        if self.tty_request_and_maybe_response:
            try:
                if self.debug:
                    print(f"sending `RTMS,{RemoteMode.OFF}' to self.tty_request_and_maybe_response", flush=True)
                print(f"RTMS,{RemoteMode.OFF}", file=self.tty_request_and_maybe_response, flush=True)
                if self.debug:
                    print('closing self.tty_request_and_maybe_response', flush=True)
                self.tty_request_and_maybe_response.close()
            finally:
                if self.debug:
                    print('setting self.tty_request_and_maybe_response to None', flush=True)
                self.tty_request_and_maybe_response = None
        if self.tty_overriding_response:
            try:
                if self.debug:
                    print('closing self.tty_overriding_response', flush=True)
                self.tty_overriding_response.close()
            finally:
                if self.debug:
                    print('setting self.tty_overriding_response to None', flush=True)
                self.tty_overriding_response = None

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    @property
    def tty_request_and_maybe_response(self):
        return self._tty_request_and_maybe_response

    @tty_request_and_maybe_response.setter
    def tty_request_and_maybe_response(self, value):
        self._tty_request_and_maybe_response = value

    @property
    def tty_overriding_response(self):
        return self._tty_overriding_response

    @tty_overriding_response.setter
    def tty_overriding_response(self, value):
        self._tty_overriding_response = value

    @property
    def product_name(self):
        self.ensure_identification_data_read()
        return self._product_name

    @product_name.setter
    def product_name(self, value):
        self._product_name = value

    @property
    def product_variant(self):
        self.ensure_identification_data_read()
        return self._product_variant

    @product_variant.setter
    def product_variant(self, value):
        self._product_variant = value

    @property
    def serial_number(self):
        self.ensure_identification_data_read()
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        self._serial_number = value

    @property
    def colorspace(self):
        return self._colorspace

    @colorspace.setter
    def colorspace(self, value):
        valid_colorspaces = self.colorspaces()
        if value not in self.colorspaces():
            raise InvalidParameterValue(f"can't set colorspace to {value}; supported spaces are {valid_colorspaces}")
        self._colorspace = value

    async def blocking_read_response(self, input_file):
        result = input_file.readline()
        return result.rstrip('\n')

    async def read_response_with_timeout(self, input_file, timeout):
        try:
            return await asyncio.wait_for(self.blocking_read_response(input_file), timeout=timeout)
        except asyncio.TimeoutError:
            raise ReadTimeout(timeout)

    def send_cmd(self, cmd, arglist):
        cmd_and_args = [cmd]
        if arglist:
            cmd_and_args.extend(arglist)
        # joined_cmd_and_args = ','.join(cmd_and_args).encode()
        try:
            # self.tty_request.write(encoded_cmd_and_args)
            joined_string = ','.join(cmd_and_args)
            print(joined_string, file=self.tty_request_and_maybe_response, flush=True)
            if self.debug:
                print(f"wrote string `{joined_string}'", flush=True)
        except Exception:
            raise WriteFailure()

    def read_response(self, cmd, arglist, expected_eccs, expected_len_response_data):
        try:
            if self.tty_overriding_response:
                response = asyncio.run(self.read_response_with_timeout(self.tty_overriding_response,
                                                                       CMD_RESULT_READ_TIMEOUT))
            else:
                response = asyncio.run(self.read_response_with_timeout(self.tty_request_and_maybe_response,
                                                                       CMD_RESULT_READ_TIMEOUT))
        except ReadTimeout as e:
            print(f"cmd `{cmd}' did not return a result within {e.timeout()} seconds")
            raise UnexpectedResponse(f"no response to `{cmd}' command (after {e.timeout()} seconds)")
        if not response:
            raise UnexpectedCmdResponse('(some sort of response)', '(empty string)', cmd,  arglist)
        split_response = response.split(',')
        ecc = split_response[0]
        response_data = split_response[1:]
        if self.debug:
            print(f"read ecc `{ecc}', response data `{response_data}'", flush=True)
        if ecc not in expected_eccs:
            raise UnexpectedCmdResponse(f"one of {expected_eccs}", ecc, cmd, arglist)
        if len(response_data) != expected_len_response_data:
            raise UnexpectedCmdResponse(f"{expected_len_response_data} comma-separated value(s)",
                                        f"{len(split_response)} values", cmd, arglist)
        return ecc, response_data

    def simple_synchronous_cmd(self, cmd, arglist, expected_eccs, expected_num_response_data):
        self.send_cmd(cmd, arglist)
        ecc, response_data = self.read_response(cmd, arglist, expected_eccs, expected_num_response_data)
        return ecc, response_data

    def remote_mode_select(self, mode):
        """
        Parameters
        ----------
        mode : RemoteMode
            turn remote mode off, on with FROM being written, or on without FROM being written
        """
        cmd = 'RTMS'
        self.simple_synchronous_cmd(cmd, [mode.value], [OK00], 0)

    def read_identification_data(self):
        """
        Returns
        -------
        product name : unicode
            probably either 'CS-2000' or 'CS-2000A'
        product variant : unicode
            either 'CS-2000' or 'CS-2000A'
        serial number : unicode
            device serial number
        """
        cmd = 'IDDR'
        ecc, response_data = self.simple_synchronous_cmd(cmd, None, [OK00], 3)
        product_name, variation_code, serial_number = response_data
        if variation_code not in [1, 2]:
            raise UnexpectedCmdResponse(f"a 0 or 1 as variation code", variation_code, cmd)
        variant = 'CS-2000' if variation_code == 0 else 'CS-2000A'
        return product_name, variant, serial_number

    def ensure_identification_data_read(self):
        if not all([self.product_name, self.product_variant, self.serial_number]):
            self.product_name, self.product_variant, self.serial_number = self.read_identification_data()

    def speed_mode_set(self, speed, internal_nd_filter=None, integration_time=None):
        # integration time is always passed to us in microseconds
        cmd = 'SPMS'
        expected_eccs = [OK00, ER00, ER17, ER30, ER32, ER34]
        speed_param = speed.value
        if speed == SpeedMode.NORMAL or speed == SpeedMode.FAST:
            internal_nd_filter_param = internal_nd_filter
            if not internal_nd_filter_param:
                internal_nd_filter_param = InternalNDFilterMode.AUTO
            if integration_time:
                raise InvalidParameterValue("can't set integration time for 'NORMAL' speed mode")
            if internal_nd_filter:
                config_string = (f"setting speed mode to `{speed.name}' and internal ND"
                                 f"filter mode to `{internal_nd_filter.name}'")
            else:
                config_string = f"setting speed mode tp `{speed.name}'"
            ecc = self.simple_synchronous_cmd(cmd, [speed_param, internal_nd_filter_param], expected_eccs, 0)
        elif speed == SpeedMode.MULTI_INTEGRATION_NORMAL or speed == SpeedMode.MULTI_INTEGRATION_FAST:
            if not integration_time:
                raise InvalidParameterValue("missing integration time for `MULTI_INTEGRATION_NORMAL' or "
                                            "`MULTI_INTEGRATION_TIME_FAST' speed mode")
            integration_time_param = integration_time / 1e6  # microseconds to seconds
            internal_nd_filter_param = internal_nd_filter
            if not internal_nd_filter_param:
                internal_nd_filter_param = InternalNDFilterMode.AUTO
            if internal_nd_filter:
                config_string = (f"setting speed mode to `{speed.name}', integration time to {integration_time_param}"
                                 f"seconds, and internal ND filter mode to `{internal_nd_filter.name}'")
            else:
                config_string = (f"setting speed mode to `{speed.name}', and internal ND filter mode"
                                 f"to `{internal_nd_filter.name}'")
            ecc = self.simple_synchronous_cmd(cmd, [speed_param, integration_time, internal_nd_filter_param],
                                              expected_eccs, 0)
        elif speed == SpeedMode.MANUAL:
            if internal_nd_filter:
                internal_nd_filter_param = internal_nd_filter
            else:
                raise InvalidParameterValue("missing internal ND filter value setting speed mode to `MANUAL'")
            if integration_time:
                integration_time_param = integration_time
            else:
                raise InvalidParameterValue("missing integration time while setting speed mode to `MANUAL'")
            config_string = f"setting speed mode to MANUAL, integration time to {integration_time} microseconds, and " \
                            f"ND filter mode to `{internal_nd_filter.name}' "
            ecc = self.simple_synchronous_cmd(cmd, [speed_param, integration_time_param, internal_nd_filter_param],
                                              expected_eccs, 0)
        else:
            raise InvalidParameterValue(f"unknown speed mode (value {speed.value}")
        raise_if_not_ok(ecc, config_string)

    def observer_read(self):
        """
        Returns
        -------
        observer: unicode
            either 'CIE 1931 2 Degree Standard Observer' or 'CIE 1964 10 Degree Standard Observer',
            both of which are keys in colour.colorimetry.datasets.cmfs.MSDS_CMFS_STANDARD_OBSERVER.
        """
        cmd = 'OBSR'
        ecc, response_data = self.simple_synchronous_cmd(cmd, None, [OK00], 1)
        obs = response_data[0]
        assert ecc == OK00
        expected_obs = {'0': 'CIE 1931 2 Degree Standard Observer',
                        '1': 'CIE 1964 10 Degree Standard Observer'}
        if obs in expected_obs:
            return expected_obs[obs]
        raise UnexpectedCmdResponse(f"0 or 1", obs, cmd, [])

    def make(self):
        """Return the meter manufacturer's name"""
        return 'Konica/Minolta'

    def model(self):
        """Return the meter model name"""
        self.ensure_identification_data_read()
        if self.product_variant == self.product_name:
            return self.product_name
        return f"{self.product_name} ({self.product_variant})"

    # serial number is a @property; see above

    def firmware_version(self):
        """Return the meter firmware version"""
        # TODO Check if it's really true that we can't get the firmware version
        return None

    def sdk_version(self):
        """Return the manufacturer's meter SDK version"""
        return None

    def adapter_version(self):
        """Return the meter adapter (proprietary SDK legal isolation layer) version"""
        return None

    def adapter_module_version(self):
        """Return the meter adapter module (Python <-> C/C++ meter adapter) version"""
        return None

    def meter_driver_version(self):
        """Return the meter driver (MeterBase concrete subclass) version"""
        return DRIVER_VERSION

    def measurement_modes(self):
        """Return the modes (EMISSIVE, reflective, &c) of measurement the meter provides"""
        return [Mode.EMISSIVE]

    def measurement_mode(self):
        """Return the measurement mode for which the meter is currently configured"""
        raise Mode.EMISSIVE

    def set_measurement_mode(self, mode):
        """Sets the measurement mode to be used for the next triggered measurement"""
        if mode != Mode.EMISSIVE:
            raise InvalidCmd("Konica/Minolta CS/2000[a] can only make emissive measurements")

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        return [IntegrationMode.ADAPTIVE, IntegrationMode.FAST, IntegrationMode.MULTI_SAMPLE_ADAPTIVE,
                IntegrationMode.MULTI_SAMPLE_FAST, IntegrationMode.FIXED]

    def set_integration_mode(self, mode, integration_time):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        # TODO figure out how to generically conceptualize internal NDs
        if mode == IntegrationMode.ADAPTIVE:
            self.speed_mode_set(SpeedMode.NORMAL)
        elif mode == IntegrationMode.MULTI_SAMPLE_ADAPTIVE:
            self.speed_mode_set(SpeedMode.MULTI_INTEGRATION_NORMAL)
        elif mode == IntegrationMode.FAST:
            self.speed_mode_set(SpeedMode.FAST, integration_time * 1e6)
        elif mode == IntegrationMode.MULTI_SAMPLE_FAST:
            self.speed_mode_set(SpeedMode.MULTI_INTEGRATION_FAST, integration_time * 1e6)
        elif mode == IntegrationMode.FIXED:
            self.speed_mode_set(SpeedMode.MANUAL, integration_time, InternalNDFilterMode.OFF)  # hope this is right

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        return [2, 242]

    def measurement_angles(self):
        # TODO implement CD-2000[A] measurement angle selection
        """Returns the set of supported discrete measurement angles, in degrees"""
        raise NotImplementedError

    def measurement_angle(self):
        """Returns the currently-set measurement angle, in degrees"""
        raise NotImplementedError

    def set_measurement_angle(self, angle):
        """Returns the currently-set measurement angle, in degrees"""
        raise NotImplementedError

    def calibration_and_calibration_expiration_time(self, mode):
        """Return the first time at which the calibration for the given mode will no longer be valid"""
        raise NotImplementedError

    def calibrate(self, wait_for_button_press=False):
        """calibrates for the current measurement mode"""
        pass

    def trigger_measurement(self):
        """Initiates measurement process of the quantity indicated by the current measurement mode"""
        cmd = 'MEAS'
        eccs = [OK00, ER00, ER10, ER17, ER51, ER52, ER71, ER83]
        ecc, response_data = self.simple_synchronous_cmd(cmd, [str(MeasurementControl.START.value)], eccs, 1)
        measurement_time = response_data[0]
        raise_if_not_ok(ecc, "triggering measurement and awaiting estimated measurement time")
        print(f"estimated measurement time is {measurement_time} seconds")
        ecc = self.read_response(cmd, [], eccs, 0)[0]
        raise_if_not_ok(ecc, "waiting for integration to complete")
        return True

    def colorspaces(self):
        """Returns the set of colorspaces in which the device can provide colorimetry"""
        return [cs.name for cs in Colorspaces]

    # n.b. as for retrieving  the colorspace, it's declared as a @property up above

    def set_colorspace(self, colorspace):
        """Sets the colorspace in which colorimetric data will be returned"""
        self.colorspace = colorspace

    def illuminants(self):
        """Returns the set of illuminants which the device can use in converting spectroradiometry to colorimetry"""
        raise NotImplementedError

    def illuminant(self):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    def set_illuminant(self, illuminant):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        raise NotImplementedError

    # TODO move higher up in the file once it has been shown to work
    def read_measurement_data(self, readout_mode):
        """Return a floating-point sequence of data resulting from last measurement"""
        cmd = 'MEDR'
        eccs = [OK00, ER00, ER02, ER10, ER17, ER20, ER51, ER52, ER71, ER83]
        result = []
        # reading out conditions is not supported at the moment
        readout_format = ReadoutDataFormat.TEXT
        if readout_mode == ReadoutMode.SPECTRAL:
            for i in range(4):
                context_string = f"reading spectral data chunk {i} (of 4)"
                ecc, response_data = self.simple_synchronous_cmd(cmd,
                                                      [str(readout_mode.value),
                                                       str(readout_format.value), str(i)],
                                                      eccs, 100 if i < 3 else 101)
                sd = response_data
                raise_if_not_ok(ecc, context_string)
                result.extend([float(f) for f in sd])
        elif readout_mode == ReadoutMode.COLORIMETRIC:
            context_string = 'reading colorimetric data'
            ecc, response_data = self.simple_synchronous_cmd(cmd,
                                                       [str(readout_mode.value),
                                                        str(readout_format.value)],
                                                       str(self.colorspace.value), 1)
            tristim = response_data
            raise_if_not_ok(ecc, context_string)
            result.extend([float(f) for f in tristim.split(',')])
        return result

    def colorimetry(self):
        """Return the colorimetry indicated by the current mode. Blocks until available"""
        return self.read_measurement_data(ReadoutMode.COLORIMETRIC)

    def spectral_range_supported(self):
        """Return the minimum and maximum wavelengths. in nanometers, to which the meter is sensitive"""
        return [380, 780]

    def spectral_resolution(self):
        """Return the difference in nanometers between spectral samples"""
        return 1

    def bandwidth_fhwm(self):
        """Return the meter's full-width half-maximum bandwidth, in nanometers"""
        raise NotImplementedError

    def spectral_distribution(self):
        """Return the spectral distribution indicated by the current mode. Blocks until available"""
        return self.read_measurement_data(ReadoutMode.SPECTRAL)
