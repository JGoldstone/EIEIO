
from datetime import timedelta
import grpc
# import metering_pb2
import metering_pb2_grpc
from services.metering.metering_pb2 import (
    IntegrationMode, Observer, MeasurementMode, ColorSpace, Illuminant,
    Instrument, MeterName,  GenericErrorCode,
    StatusRequest, ConfigurationRequest, CalibrationRequest, CaptureRequest,
    ColorimetricConfiguration, RetrievalRequest)
from eieio.meter.xrite.i1pro import I1Pro


def fprint(x, **kwargs):
    print(x, flush=True, **kwargs)


def print_if_not_blank(value, label):
    if value:
        fprint(f"{label}: {value}")


def print_meter_description(meter_desc):
    print_if_not_blank(meter_desc.name, "name")
    # if meter_desc.HasField('name'):
    #     print(f"name : {meter_desc.name}")
    if meter_desc.instrument != Instrument.MISSING_INSTRUMENT:
        print(f"instrument: {meter_desc.instrument.Name()}")
    print_if_not_blank(meter_desc.make, 'make')
    print_if_not_blank(meter_desc.model, 'model')
    print_if_not_blank(meter_desc.serial_number, 'serial number')
    print_if_not_blank(meter_desc.firmware_version, 'firmware version')
    print_if_not_blank(meter_desc.sdk_version, 'SDK version')
    print_if_not_blank(meter_desc.adapter_version, 'adapter version')
    print_if_not_blank(meter_desc.adapter_module_version, 'adapter [Python] module version')
    for measurement_mode in meter_desc.supported_measurement_modes:
        print_if_not_blank(MeasurementMode.Name(measurement_mode), 'supported measurement mode')
    print_if_not_blank(meter_desc.current_measurement_mode, 'current measurement mode')
    for integration_mode in meter_desc.supported_integration_modes:
        print_if_not_blank(IntegrationMode.Name(integration_mode), 'supported integration mode')
    print_if_not_blank(meter_desc.current_integration_mode, 'current integration mode')
    for measurement_angle in meter_desc.supported_measurement_angles:
        print_if_not_blank(measurement_angle, 'supported measurement angle')
    print_if_not_blank(meter_desc.current_measurement_angle, 'current measurement angle')


def pretty_generic_error(generic_error_code, details):
    value = None
    if generic_error_code == GenericErrorCode.MISSING_GENERIC_ERROR_CODE:
        value = 'unparsable generic error: missing generic error code'
    elif generic_error_code == GenericErrorCode.DEVICE_DISCONNECTED:
        value = 'Device disconnected'
    elif generic_error_code == GenericErrorCode.DEVICE_BUSY:
        value = 'Device busy'
    elif generic_error_code == GenericErrorCode.DEVICE_UNRESPONSIVE:
        value = 'Device unresponsive'
    elif generic_error_code == GenericErrorCode.UNCATEGORIZED_ERROR:
        value = 'Uncategorizable error'
    if details:
        value = f"{value}: {details}"
    return value


def pretty_print_calibration_error(error):
    if error.HasField('generic_error_code'):
        return pretty_generic_error(error.generic_error_code, error.details)
    if not error.HasField('calibration_specific_error_code'):
        return "unparseable calibration error: neither generic nor calibration_specific"
    # code = error.calibration_specific_error_code
    # At the moment there are no calibration-specific errors, so...
    return "unparseable calibration error: calibration_specific error indicated, but there are no such errors"


def pretty_print_retrieval_error(error):
    if error.HasField('generic_error_code'):
        return pretty_generic_error(error.generic_error_code, error.details)
    if not error.HasField('retrievable_specific_error_code'):
        return "unparseable retrievable error: neither generic nor calibration_specific"
    # code = error.calibration_specific_error_code
    # At the moment there are no calibration-specific errors, so...
    return "unparseable calibration error: calibration_specific error indicated, but there are no such errors"


def pretty_print_colorimetry(measurement):
    color_space = ColorSpace.Name(measurement.color_space)
    illuminant = Illuminant.Name(measurement.illuminant)
    if color_space not in ['CIE_XYZ', 'CIE_xyY', 'RxRyRz', 'RGB', 'Lv_xy', 'Y_xy', 'Lv_T_duv',
                           'Dominant_wavelength_and_excitation_purity']:
        color_space = f"{color_space} ({illuminant})"
    first = float(measurement.first)
    second = float(measurement.second)
    third = float(measurement.third)
    print(f"{color_space} / {illuminant}: {first:5.4f} {second:5.4f} {third:5.4}")


def pretty_print_spectrum(measurement):
    if measurement.wavelengths:
        for i, wavelength in enumerate(measurement.wavelengths):
            print(f"{wavelength:3}nm: {measurement.values[i]}")

def promptForCalibrationPositioning(prompt=None):
    """Prompt the user to set the meter up for calibration (e.g. put on calibration tile)"""
    print('Position i1Pro on calibration tile, and press RETURN: ', flush=True, end='')
    _ = input()
    print(flush=True)

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        client = metering_pb2_grpc.MeteringStub(channel)
        # meter_name = MeterName(name="1099162")  # i1Pro2
        # meter_name = MeterName(name="108454")  # i1Pro (original)
        meter_name = MeterName(name="2004141")  # i1Pro3
        # Get and print meter status
        status_request = StatusRequest(meter_name=meter_name)
        status_response = client.ReportStatus(status_request)
        print_meter_description(status_response.description)
        # calibrate if need be
        used_tile = False
        needs_tile_positioning = status_response.description.model == 'i1pro' and not used_tile
        needs_target_positioning = False
        for used_and_left in status_response.description.calibrations_used_and_left:
            mode = used_and_left.mode
            left = used_and_left.left
            if left.ToTimedelta() < timedelta(hours=1):
                calibration_request = CalibrationRequest(meter_name=meter_name, mode=mode)
                if needs_tile_positioning:
                    I1Pro.prompt_for_calibration_positioning("place i1Pro on tile and press RETURN")
                    needs_tile_positioning = False
                    needs_target_positioning = True
                calibration_response = client.Calibrate(calibration_request)
        if needs_target_positioning:
            I1Pro.prompt_for_target_positioning("orient i1Pro towards target and press RETURN")
            calibration_request = CalibrationRequest(meter_name=meter_name)
            calibration_response = client.Calibrate(calibration_request)
            if calibration_response.HasField('error'):
                raise RuntimeError(f"{pretty_print_calibration_error(calibration_response.error)}")
        configuration_request = ConfigurationRequest(meter_name=meter_name,
                                                     observer=Observer.TWO_DEGREE_1931,
                                                     measurement_mode = MeasurementMode.EMISSIVE,
                                                     illuminant=Illuminant.D65,
                                                     color_space=ColorSpace.CIE_xyY)
        configuration_response = client.Configure(configuration_request)
        if configuration_response.error:
            print("---> not everything went well with the configuration request")
        # capture the stimulus
        fprint('about to send capture request')
        capture_request = CaptureRequest(meter_name=meter_name)
        fprint('send capture request, waiting for capture response')
        capture_response = client.Capture(capture_request)
        fprint('received capture response')
        if capture_response.estimated_duration:
            fprint(f"estimated time is {capture_response.estimated_duration}")
        else:
            fprint('no time estimate (assuming zero)')
        # retrieve spectral data and colorimetry
        color_spaces = [ColorSpace.CIE_XYZ, ColorSpace.CIE_xyY]
        illuminants = [Illuminant.D65, Illuminant.D65]
        configs = []
        for cs, il in zip(color_spaces, illuminants):
            config = ColorimetricConfiguration(color_space=cs, illuminant=il)
            configs.append(config)
        fprint(f"{len(configs)} colorimetric configs in retrieve request")
        retrieval_request = RetrievalRequest(meter_name=meter_name,
                                             spectrum_requested=True,
                                             colorimetric_configurations=configs)
        retrieval_response = client.Retrieve(retrieval_request)
        if retrieval_response.HasField('spectral_measurement'):
            pretty_print_spectrum(retrieval_response.spectral_measurement)
        for tristimulus_measurement in retrieval_response.tristimulus_measurements:
            pretty_print_colorimetry(tristimulus_measurement)
        fprint('client is DONE')
