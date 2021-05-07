# -*- coding: utf-8 -*-
"""
Unit tests for the stand-in tristimulus colorimetry class
================================

Test the :class:`spectral_measurement.session.TristimulusColorimetryMeasurement` class.

"""

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
]

import unittest
from pathlib import Path
from eieio.measurement.old_colorimetry import TristimulusColorimetryMeasurement

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
        self.assertRaises(FileNotFoundError, TristimulusColorimetryMeasurement,
                          f"not_{TEST_COLX_PATH}", "XYZ", (0.3, 0.3, 0.3))

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
