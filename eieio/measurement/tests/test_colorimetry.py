import unittest

from colour.colorimetry.datasets.cmfs import MSDS_CMFS_STANDARD_OBSERVER
from colour.models.common import COLOURSPACE_MODELS
from colour.colorimetry.datasets.illuminants.chromaticity_coordinates import CCS_ILLUMINANTS
from eieio.measurement.colorimetry import Colorimetry

DEFAULT_TEST_OBS = 'CIE 1931 2 Degree Standard Observer'
DEFAULT_TEST_CS = 'CIE XYZ'
DEFAULT_TEST_IL = 'D65'
DEFAULT_TEST_VALS = [0, 1, 2]
DEFAULT_TEST_ORIGIN = 'MEASURED'
DEFAULT_DEVICE_NAME = 'i1Pro2_1099162'

C0 = {'observer': DEFAULT_TEST_OBS,
      'color_space': DEFAULT_TEST_CS,
      'derivation': DEFAULT_TEST_ORIGIN,
      'illuminant': DEFAULT_TEST_IL,
      'device_name': DEFAULT_DEVICE_NAME,
      'values': DEFAULT_TEST_VALS}

C1 = {'observer': DEFAULT_TEST_OBS,
      'color_space': DEFAULT_TEST_CS,
      'derivation': DEFAULT_TEST_ORIGIN,
      'illumination': DEFAULT_TEST_IL,
      'device_name': DEFAULT_DEVICE_NAME,
      'values': [1, 2, 3]}


class TestColorimetry(unittest.TestCase):

    def test_bad_observer_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry('foo', DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                        DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN)

    def test_good_observers(self):
        for obs in MSDS_CMFS_STANDARD_OBSERVER:
            self.assertIsNotNone(Colorimetry(obs, DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                                             DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN))

    def test_bad_color_space_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry(DEFAULT_TEST_OBS, 'foo', DEFAULT_TEST_IL,
                        DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN)

    def text_good_color_spaces(self):
        for cs in COLOURSPACE_MODELS:
            self.assertIsNotNone(Colorimetry(DEFAULT_TEST_OBS, cs, DEFAULT_TEST_IL,
                                             DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN))

    def test_bad_illuminant_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry(DEFAULT_TEST_OBS, DEFAULT_TEST_CS, 'foo',
                        DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN)

    def test_bad_illum_for_obs_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry('CIE 1964 10 Degree Standard Observer', DEFAULT_TEST_CS, 'ACES',
                        DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN)

    def text_good_illuminants(self):
        for obs in CCS_ILLUMINANTS.keys():
            for il in CCS_ILLUMINANTS[obs]:
                self.assertIsNotNone(Colorimetry(obs, DEFAULT_TEST_CS, il,
                                                 DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN))

    def test_too_few_values_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry(DEFAULT_TEST_OBS, DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                        [0, 1], origin=DEFAULT_TEST_ORIGIN)

    def test_too_many_values_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry(DEFAULT_TEST_OBS, DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                        [0, 1, 2, 3], origin=DEFAULT_TEST_ORIGIN)

    def test_good_values(self):
        self.assertIsNotNone(Colorimetry(DEFAULT_TEST_OBS, DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                                         DEFAULT_TEST_VALS, origin=DEFAULT_TEST_ORIGIN))

    def test_bad_origin_raises(self):
        with self.assertRaises(ValueError):
            Colorimetry(DEFAULT_TEST_OBS, DEFAULT_TEST_CS, DEFAULT_TEST_IL,
                        DEFAULT_TEST_VALS, origin='foo')


if __name__ == '__main__':
    unittest.main()
