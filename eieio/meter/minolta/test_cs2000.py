import unittest
from tempfile import NamedTemporaryFile
from eieio.meter.minolta.cs2000 import CS2000

TEST_AGAINST_PRERECORDED_CS2000_OUTPUT = False
TEST_WITH_DEBUG_OUTPUT = True
POST_COMMAND_SETTLE_TIME = 0
REQUEST_SINK = '/dev/null'

def write_meas_response(f, measurement_time=2):
    if measurement_time != round(measurement_time):
        pre_round_measurement_time = measurement_time
        measurement_time = round(measurement_time)
        print(f"rounded measurement time from {pre_round_measurement_time} to {measurement_time}")
    f.write(f"OK00,{measurement_time}\n".encode())
    f.write(b'OK00')
    f.flush()

def write_medr_response(f):
    for (min_lambda, max_lambda) in [(380, 480), (480, 580), (580, 680), (680, 781)]:
        f.write(b'OK00')
        for lambda_ in range(min_lambda, max_lambda):  # don't forget that in python lambda is a keyword
            unicode_value = f",{lambda_:.4e}".replace('+0', '+')
            bytes_value = unicode_value.encode()
            f.write(bytes_value)
        f.write(b'\n')
    f.flush()


class MyTestCase(unittest.TestCase):
    def real_or_simulated_device(self, temp_file_name):
        print('\ntesting CS2000 constructor')
        if TEST_AGAINST_PRERECORDED_CS2000_OUTPUT:
            print(f"creating CS2000 ctor with args `{REQUEST_SINK}' and `{temp_file_name}'")
            device = CS2000(meter_request_and_maybe_response_path=REQUEST_SINK,
                            meter_response_override_path=temp_file_name,
                            debug=TEST_WITH_DEBUG_OUTPUT)
        else:
            device = CS2000(debug=TEST_WITH_DEBUG_OUTPUT,
                            post_command_settle_time=POST_COMMAND_SETTLE_TIME)
        return device

    # def test_spectral_range(self):
    #     print('\ntesting CS2000 spectral range')
    #     with NamedTemporaryFile() as temp_file:
    #         device = self.real_or_simulated_device(temp_file.name)
    #         self.assertEqual([380, 780], device.spectral_range_supported())
    #
    # def test_spectral_resolution(self):
    #     print('\ntesting CS2000 spectral resolution')
    #     with NamedTemporaryFile() as temp_file:
    #         device = self.real_or_simulated_device(temp_file.name)
    #         self.assertEqual(1, device.spectral_resolution())
    #
    # def test_calibrate(self):
    #     print('\ntesting CS2000 calibrate')
    #     with NamedTemporaryFile() as temp_file:
    #         device = self.real_or_simulated_device(temp_file.name)
    #         try:
    #             device.calibrate()
    #         except Exception:
    #             self.fail("CS2000 failed calibration (which should be a no-op")
    #
    # def test_read_serial_numner(self):
    #     print('\ntesting CS2000 read serial number')
    #     with NamedTemporaryFile() as temp_file:
    #         write_meas_response(temp_file)
    #         device = self.real_or_simulated_device(temp_file.name)
    #         print(f"device serial number is {device.serial_number}")
    #         self.assertTrue(device.serial_number != '')

    def test_trigger_measurement(self):
        print('\ntesting CS2000 trigger measurement')
        with NamedTemporaryFile() as temp_file:
            write_meas_response(temp_file)
            device = self.real_or_simulated_device(temp_file.name)
            self.assertTrue(device.trigger_measurement())

    # def test_read_spectral_distribution(self):
    #     print('\ntesting CS2000 read spectral distribution')
    #     with NamedTemporaryFile() as temp_file:
    #         write_medr_response(temp_file)
    #         device = self.real_or_simulated_device(temp_file.name)
    #         [min_lambda, max_lambda] = device.spectral_range_supported()
    #         inc_lambda = device.spectral_resolution()
    #         num_lambdas = (max_lambda+1-min_lambda)
    #         self.assertEqual((num_lambdas - 1) % inc_lambda, 0)
    #         device.trigger_measurement()
    #         sd = device.spectral_distribution()
    #         self.assertEqual(num_lambdas, len(sd))
    #         expected_sd = [float(lambda_) for lambda_ in range(min_lambda, max_lambda + 1, inc_lambda)]
    #         self.assertEqual(expected_sd, sd)


if __name__ == '__main__':
    unittest.main()
