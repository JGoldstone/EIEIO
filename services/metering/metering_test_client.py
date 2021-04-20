import grpc
# import metering_pb2
import metering_pb2_grpc
from services.metering.metering_pb2 import (
    MeterName, Instrument, MeasurementMode, IntegrationMode, StatusRequest
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


if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        client = metering_pb2_grpc.MeteringStub(channel)
        meter_name = MeterName(name="i1Pro2_0")
        request = StatusRequest(meter_name=meter_name)
        response = client.ReportStatus(request)
        print_meter_description(response.description)
