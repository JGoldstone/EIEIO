import platform
from time import sleep
from enum import Enum
from collections import deque
from serial import Serial

from utilities.log import LogEvent
from eieio.meter.meter_abstractions import MeterError, SpectroradiometerBase
from services.metering.metering_pb2 import MeasurementMode, IntegrationMode, Observer, ColorSpace, Illuminant
from google.protobuf.duration_pb2 import Duration

DRIVER_VERSION = '0.0.2b'
CMD_RESULT_READ_TIMEOUT = 0

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

CS2000_TO_METERING_COLOR_SPACE_MAP = {
    '0': ColorSpace.CIE_xyY,
    '1': ColorSpace.CIE_uv_1976,
    '2': ColorSpace.Lv_T_duv,
    '3': ColorSpace.CIE_XYZ,
    '4': ColorSpace.Dominant_wavelength_and_excitation_purity
}

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


def cs2000_tty_path():
    return '/dev/tty.usbmodem12345678901' if platform.system().lower() == 'darwin' else '/dev/ttyACM0'


def raise_if_not_ok(ecc, context):
    if ecc != OK00:
        raise UnexpectedResponse(f"expected response {OK00}, saw {ecc} (while {context})")


class CS2000(SpectroradiometerBase):

    def print_if_debug(self, str_):
        if self.debug:
            print(str_, flush=True)

    def low_level_write(self, stream_, str_):
        with_cr = str_+'\r'
        stream_.write(with_cr.encode())
        stream_.flush()

    def low_level_read(self, stream_):
        byte_result = stream_.readline()
        string_result = byte_result.decode()
        if string_result and len(string_result) > 0:
            while True:
                cr_ix = string_result.find('\r')
                if cr_ix >= 0:
                    chunk = string_result[:cr_ix]
                    self.print_if_debug(f"saw chunk `{chunk}'")
                    if len(self.partial_token_buffer) > 0:
                        self.print_if_debug('there is a partial token buffer')
                        self.partial_token_buffer += chunk
                        self.print_if_debug(f"now-completed partial token buffer is `{self.partial_token_buffer}'")
                        self.read_input_queue.appendleft(self.partial_token_buffer)
                        self.partial_token_buffer = ''
                    else:
                        # got a complete line, then
                        self.print_if_debug(f"adding chunk `{chunk}' to self.read_input_queue")
                        self.read_input_queue.appendleft(chunk)
                    string_result = string_result[cr_ix+1:]
                else:
                    self.print_if_debug(f"adding `{string_result}' to existing partial token buffer `{self.partial_token_buffer}'")
                    self.partial_token_buffer += string_result
                    break
        if len(self.read_input_queue) > 0:
            result = self.read_input_queue.pop()
            self.print_if_debug(f"popping off and returning `{result}'")
            return result
        else:
            return ''

    def open_internal(self, path):
        self.print_if_debug(f"opening connection to CS2000 at `{path}'")
        ser = Serial(path, 115200, timeout=1)
        if not ser.is_open:
            raise RuntimeError("can't find minolta")
        self.print_if_debug(f"opened connection to CS2000 at `{path}' OK")
        return ser

    def open(self, primary_path, secondary_path):
        self.tty_request_and_maybe_response = self.open_internal(primary_path)
        if secondary_path:
            self.tty_overriding_response = self.open_internal(secondary_path)

    def settle_after_command(self, cmd):
        if self.post_command_settle_time and self.post_command_settle_time > 0:
            self.print_if_debug(f"pausing {self.post_command_settle_time} second(s) after sending {cmd} command")
            sleep(self.post_command_settle_time)

    def __init__(self, meter_request_and_maybe_response_path=cs2000_tty_path(),
                 meter_response_override_path=None, post_command_settle_time=0, debug=False):
        self._post_command_settle_time = None
        self.post_command_settle_time = post_command_settle_time
        self._debug = None
        self.debug = debug
        self._product_name = None
        self.product_name = None
        self._product_variant = None
        self.product_variant = None
        self._serial_number = '123456'
        self.serial_number = '123456'
        self._integration_mode = IntegrationMode.NORMAL_ADAPTIVE
        self.integration_mode = IntegrationMode.NORMAL_ADAPTIVE
        self._observer = None
        # TODO figure out why the automatically generated setter doesn't work
        # self.observer = None
        self.color_space = ColorSpace.CIE_xyY
        self.delim = '\n'
        self._tty_request_and_maybe_response = None
        self.tty_request_and_maybe_response = None
        self._tty_overriding_response = None
        self.tty_overriding_response = None
        self.partial_token_buffer = ''
        self.read_input_queue = deque()
        self.open(meter_request_and_maybe_response_path, meter_response_override_path)
        rmts_arg = RemoteMode.ON_WRITING_FROM.value
        self.print_if_debug(f"Sending `RMTS,{rmts_arg}' to `{meter_request_and_maybe_response_path}'")
        self.low_level_write(self.tty_request_and_maybe_response, f"RMTS,{rmts_arg}")
        self.print_if_debug(f"Sent RMTS,{rmts_arg} to `{meter_request_and_maybe_response_path}'")
        self.settle_after_command(f"`RMTS,{rmts_arg}'")
        response = self.tty_request_and_maybe_response.readline()
        self.print_if_debug("looking for (specifically RMTS) device response...")
        self.print_if_debug(f"RMTS response from device is `{response}'")

    def __del__(self):
        if self.tty_request_and_maybe_response:
            try:
                rmts_arg = RemoteMode.OFF.value
                self.print_if_debug(f"sending `RMTS,{rmts_arg}' to self.tty_request_and_maybe_response")
                self.low_level_write(self.tty_request_and_maybe_response, f"RMTS,{rmts_arg}")
                # print(f"RMTS,{rmts_arg}", file=self.tty_request_and_maybe_response, flush=True)
                if self.post_command_settle_time > 0:
                    self.print_if_debug(f"pausing {self.post_command_settle_time} second(s) after sending command")
                    sleep(self.post_command_settle_time)
                self.print_if_debug('closing self.tty_request_and_maybe_response')
                self.tty_request_and_maybe_response.close()
            finally:
                self.print_if_debug('setting self.tty_request_and_maybe_response to None')
                self.tty_request_and_maybe_response = None
        if self.tty_overriding_response:
            try:
                self.print_if_debug('closing self.tty_overriding_response')
                self.tty_overriding_response.close()
            finally:
                self.print_if_debug('setting self.tty_overriding_response to None')
                self.tty_overriding_response = None

    @property
    def post_command_settle_time(self):
        return self._post_command_settle_time

    @post_command_settle_time.setter
    def post_command_settle_time(self, value):
        self._post_command_settle_time = value

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
        if not self._product_name:
            self._product_name, self._product_variant, self._serial_number = ['CS-2000', 'CS-2000', '123456']
        return self._product_name

    @product_name.setter
    def product_name(self, value):
        self._product_name = value

    @property
    def product_variant(self):
        if not self._product_variant:
            self._product_name, self._product_variant, self._serial_number = ['CS-2000', 'CS-2000', '123456']
        return self._product_variant

    @product_variant.setter
    def product_variant(self, value):
        self._product_variant = value

    def serial_number(self):
        return '123456'
        # if not self._serial_number:
        #     _, _, self._serial_number = self.read_identification_data()
        #     # self._product_name, self._product_variant, self._serial_number = ['CS-2000', 'CS-2000', '123456']
        # return self._serial_number

    def set_serial_number(self, value):
        self._serial_number = value

    def observer(self):
        return self._observer

    def set_observer(self, value):
        self._observer = value

    def color_space(self):
        return self.color_space

    def set_color_space(self, value):
        if value not in self.color_spaces():
            raise InvalidParameterValue(f"can't set color space to {ColorSpace.Name(value)}; "
            f"supported spaces are {[ColorSpace.Name(cs) for cs in self.color_spaces()]}")
        self.color_space = value

    def send_cmd(self, cmd, arglist):
        cmd_and_args = [cmd]
        if arglist:
            cmd_and_args.extend(arglist)
        try:
            joined_string = ','.join(cmd_and_args)
            self.low_level_write(self.tty_request_and_maybe_response, joined_string)
            self.print_if_debug(f"wrote string `{joined_string}'")
            if self.post_command_settle_time > 0:
                self.print_if_debug(f"pausing {self.post_command_settle_time} second(s) after sending command")
                sleep(self.post_command_settle_time)
        except Exception:
            raise WriteFailure()

    def read_response(self, cmd, arglist, expected_eccs, expected_len_response_data):
        while True:
            response = self.low_level_read(self.tty_request_and_maybe_response)
            if response:
                break
            #print("didn't see anything, sleeping for a sec")
            #sleep(1)
        if not response:
            raise UnexpectedCmdResponse('(some sort of response)', '(empty string)', cmd,  arglist)
        # split_response = response.rstrip('\r').split(',')
        self.print_if_debug(f"unsplit response is `{response}'")
        split_response = response.split(',')
        ecc = split_response[0]
        response_data = split_response[1:]
        self.print_if_debug(f"read ecc `{ecc}', response data `{response_data}'")
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
        cmd = 'RMTS'
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
        if variation_code not in ['0', '1', '2']:
            raise UnexpectedCmdResponse(f"a 0, 1, or 2 as variation code", variation_code, cmd)
        variant = 'CS-2000' if variation_code == 0 else 'CS-2000A'
        return product_name, variant, serial_number

    # def ensure_identification_data_read(self):
    #     if not all([self.product_name, self.product_variant, self.serial_number]):
    #         self.product_name, self.product_variant, self.serial_number = self.read_identification_data()

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
        new_obs = {'0': Observer.CIE_1931_2_DEGREE_STANDARD_OBSERVER,
                   '1': Observer.CIE_1964_10_DEGREE_STANDARD_OBSERVER}
        self.set_observer(new_obs[obs])
        expected_obs = {'0': 'CIE 1931 2 Degree Standard Observer',
                        '1': 'CIE 1964 10 Degree Standard Observer'}
        if obs in expected_obs:
            return expected_obs[obs]
        raise UnexpectedCmdResponse(f"0 or 1", obs, cmd, [])

    def observers(self):
        return [Observer.CIE_1931_2_DEGREE_STANDARD_OBSERVER, Observer.CIE_1964_10_DEGREE_STANDARD_OBSERVER]

    def make(self):
        """Return the meter manufacturer's name"""
        return 'Konica/Minolta'

    def model(self):
        """Return the meter model name"""
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
        """Return the modes (EMISSIVE, reflective, &c) of spectral_measurement the meter provides"""
        return [MeasurementMode.EMISSIVE]

    def measurement_mode(self):
        """Return the spectral_measurement mode for which the meter is currently configured"""
        return MeasurementMode.EMISSIVE

    def set_measurement_mode(self, mode):
        """Sets the spectral_measurement mode to be used for the next triggered spectral_measurement"""
        if mode != MeasurementMode.EMISSIVE:
            raise InvalidCmd("Konica/Minolta CS/2000[a] can only make emissive measurements")

    def integration_modes(self):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        return [IntegrationMode.NORMAL_ADAPTIVE]

    def integration_mode(self):
        return IntegrationMode.NORMAL_ADAPTIVE

    def set_integration_mode(self, mode, integration_time):
        """Return the types of integration (e.g. fixed, adaptive, &c) supported"""
        # TODO figure out how to generically conceptualize internal NDs
        if mode == IntegrationMode.NORMAL_ADAPTIVE:
            self.speed_mode_set(SpeedMode.NORMAL)
        elif mode == IntegrationMode.MULTI_SAMPLE_NORMAL_ADAPTIVE:
            self.speed_mode_set(SpeedMode.MULTI_SAMPLE_NORMAL)
        elif mode == IntegrationMode.FAST_ADAPTIVE:
            self.speed_mode_set(SpeedMode.FAST, integration_time * 1e6)
        elif mode == IntegrationMode.MULTI_SAMPLE_FAST_ADAPTIVE:
            self.speed_mode_set(SpeedMode.MULTI_INTEGRATION_FAST, integration_time * 1e6)
        elif mode == IntegrationMode.FIXED:
            self.speed_mode_set(SpeedMode.MANUAL, integration_time, InternalNDFilterMode.OFF)  # hope this is right
        self.integration_mode = mode

    def integration_time_range(self):
        """Return the minimum and maximum integration time supported"""
        return [2, 242]

    def calibration_used_and_left(self):
        return Duration(seconds=1), Duration(seconds=24*60*60*52)

    def measurement_angles(self):
        # TODO implement CD-2000[A] spectral_measurement angle selection
        """Returns the set of supported discrete spectral_measurement angles, in degrees"""
        return [2.0]

    def measurement_angle(self):
        """Returns the currently-set spectral_measurement angle, in degrees"""
        return 2.0

    def set_measurement_angle(self, angle):
        """Returns the currently-set spectral_measurement angle, in degrees"""
        pass

    def calibrate(self, wait_for_button_press=False):
        """calibrates for the current spectral_measurement mode"""
        pass

    def trigger_measurement(self, log=None):
        """Initiates spectral_measurement process of the quantity indicated by the current spectral_measurement mode"""
        cmd = 'MEAS'
        eccs = [OK00, ER00, ER10, ER17, ER51, ER52, ER71, ER83]
        if log:
            log.add(LogEvent.METER_TRIGGER, 'triggering Minolta CS-2000[A]')
        ecc, response_data = self.simple_synchronous_cmd(cmd, [str(MeasurementControl.START.value)], eccs, 1)
        measurement_time = response_data[0]
        raise_if_not_ok(ecc, "triggering spectral_measurement and awaiting estimated spectral_measurement time")
        sleep_time = int(measurement_time) + 2
        if log:
            log.add(LogEvent.METER_TRIGGER, f"triggered Minolta CS_2000A, estimated spectral_measurement time "
                                      f"{measurement_time} seconds")
            log.add(LogEvent.METER_TRIGGER, f"will wait {sleep_time} seconds before attempting CS-2000[A] read")
        sleep(sleep_time)
        ecc = self.read_response(cmd, [], eccs, 0)[0]
        raise_if_not_ok(ecc, "waiting for integration to complete")
        return True

    def color_spaces(self):
        """Returns the set of color spaces in which the device can provide colorimetry"""
        return [ColorSpace.CIE_XYZ, ColorSpace.CIE_xyY, ColorSpace.CIE_Luv,
                ColorSpace.Lv_T_duv,
                ColorSpace.Dominant_wavelength_and_excitation_purity]
                # ColorSpace.CIE_XYZ_10, ColorSpace.CIE_xyY_10, ColorSpace.CIE_Luv_10,
                # ColorSpace.Lv_T_duv_10,
                # ColorSpace.Dominant_wavelength_and_excitation_purity_10]

    def illuminants(self):
        """Returns the set of illuminants which the device can use in converting spectroradiometry to colorimetry"""
        return [Illuminant.D65]

    def illuminant(self):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        return Illuminant.D65

    def set_illuminant(self, illuminant):
        """Returns the illuminant with which the device will convert spectroradiometry to colorimetry"""
        pass

    # TODO move higher up in the file once it has been shown to work
    def read_measurement_data(self, readout_mode):
        """Return a floating-point sequence of data resulting from last spectral_measurement"""
        cmd = 'MEDR'
        eccs = [OK00, ER00, ER02, ER10, ER17, ER20, ER51, ER52, ER71, ER83]
        result = []
        # reading out conditions is not supported at the moment
        readout_format = ReadoutDataFormat.TEXT
        if readout_mode == ReadoutMode.SPECTRAL:
            for i in range(1, 5):
                context_string = f"reading spectral data chunk {i} (of 4)"
                ecc, response_data = self.simple_synchronous_cmd(cmd,
                                                      [str(readout_mode.value),
                                                       str(readout_format.value), str(i)],
                                                      eccs, 100 if i < 4 else 101)
                sd = response_data
                raise_if_not_ok(ecc, context_string)
                result.extend([float(f) for f in sd])
        elif readout_mode == ReadoutMode.COLORIMETRIC:
            context_string = 'reading colorimetric data'
            cs = [k for k, v in CS2000_TO_METERING_COLOR_SPACE_MAP.items() if v == self.color_space][0]
            ecc, response_data = self.simple_synchronous_cmd(cmd,
                                                       [str(readout_mode.value),
                                                        str(readout_format.value)],
                                                       cs, 1)
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

    def prompt_for_calibration_positioning(self):
        pass

    def prompt_for_target_positioning(self):
        pass

