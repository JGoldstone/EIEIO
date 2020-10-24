import unittest
from pathlib import Path
from measurement.tristim_colorimetry import TristimulusColorimetryMeasurement

TEST_COLX_PATH = '/tmp/foo.colx'

class MyTestCase(unittest.TestCase):

    def setUp(self):
        with open(TEST_COLX_PATH, 'w') as tf:
            print('[attributes]', file=tf)
            print('colorspace = "CIEXYZ"', file=tf)
            print('[payload]', file=tf)
            print('values = [1, 3, 7]', file=tf)

    def tearDown(self):
        Path(TEST_COLX_PATH).unlink(missing_ok=True)

    def test_nonexistent_file_raises(self):
        self.assertRaises(FileNotFoundError, TristimulusColorimetryMeasurement, f"not_{TEST_COLX_PATH}", "XYZ", (0.3, 0.3, 0.3))

    def test_existing_file_loads(self):
        loaded = TristimulusColorimetryMeasurement(TEST_COLX_PATH)
        self.assertEqual(loaded.colorspace, 'CIEXYZ')
        self.assertEqual(loaded.values, [1, 3, 7])

    def test_args_override_file(self):
        loaded = TristimulusColorimetryMeasurement(TEST_COLX_PATH, colorspace='CIELAB', values=[2, 4, 8])
        self.assertEqual(loaded.colorspace, 'CIELAB')
        self.assertEqual(loaded.values, [2, 4, 8])


if __name__ == '__main__':
    unittest.main()
