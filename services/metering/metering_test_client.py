import grpc
# import metering_pb2
import metering_pb2_grpc
from services.metering.metering_pb2 import (
    GenericErrorCode,
    MeterName, Instrument, MeasurementMode, IntegrationMode,
    StatusRequest, CalibrationRequest, CaptureRequest
)

def print_if_not_blank(value, label):
    if value:
        print(f"{label}: {value}")

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

def pretty_calibration_error(error):
    if error.HasField('generic_error_code'):
        return pretty_generic_error(error.generic_error_code, error.details)
    if not error.HasField('calibration_specific_error_code'):
        return "unparseable calibration error: neither generic nor calibration_specific"
    # code = error.calibration_specific_error_code
    # At the moment there are no calibration-specific errors, so...
    return "unparseable calibration error: calibration_specific error indicated, but there are no such errors"

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        client = metering_pb2_grpc.MeteringStub(channel)
        meter_name = MeterName(name="i1Pro2_0")
        status_request = StatusRequest(meter_name=meter_name)
        status_response = client.ReportStatus(status_request)
        print_meter_description(status_response.description)
        calibration_request = CalibrationRequest(meter_name=meter_name)
        calibration_response = client.Calibrate(calibration_request)
        if calibration_response.HasField('error'):
            raise RuntimeError(f"{pretty_calibration_error(calibration_response.error)}")
        capture_request = CaptureRequest(meter_name=meter_name)
        capture_response = client.Capture(capture_request)

