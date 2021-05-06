import unittest
from tempfile import NamedTemporaryFile

from eieio.measurement.colorimetry import Colorimetry
from eieio.measurement.measurement import Measurement

OBS = 'CIE 1931 2 Degree Standard Observer'
CS0 = 'CIE XYZ'
CS1 = 'CIE xyY'
IL = 'D65'
VALS = [0.11, 0.22, 0.67]
ORIG = 'SYNTHESIZED'
C0 = Colorimetry(observer=OBS, color_space=CS0, illuminant=IL, values=VALS, origin=ORIG)
C1 = Colorimetry(observer=OBS, color_space=CS1, illuminant=IL, values=VALS, origin=ORIG)


class TestMeasurement(unittest.TestCase):
    def test_json_round_trip(self):
        m = Measurement()
        m.insert_colorimetry(C0)
        m.insert_colorimetry(C1)
        ck_c = m.comma_keyed_colorimetry()
        self.assertEqual(2, len(ck_c))
        js_c = m.extra_metadata_as_json()
        c_rt = Measurement.extract_colorimetry_from_json(js_c)
        self.assertEqual(len(ck_c), len(c_rt))
        c0_key = (C0.observer, C0.color_space, C0.illuminant)
        self.assertIn(c0_key, c_rt)
        c0_rt = c_rt[c0_key]
        self.assertEqual(C0, c0_rt)
        c1_key = (C1.observer, C1.color_space, C1.illuminant)
        self.assertIn(c1_key, c_rt)
        c1_rt = c_rt[c1_key]
        self.assertEqual(C1, c1_rt)

    def test_comments_round_trip(self):
        m0 = Measurement()
        m0.insert_colorimetry(C0)
        m0.insert_colorimetry(C1)
        m0.path = NamedTemporaryFile().name
        m0.write()
        m1 = Measurement()
        m1.path = m0.path
        m1.read()
        self.assertEqual(2, len(m1.colorimetry))
        c0_key = (C0.observer, C0.color_space, C0.illuminant)
        self.assertIn(c0_key, m1.colorimetry)
        self.assertEqual(C0, m1.colorimetry[c0_key])
        c1_key = (C1.observer, C1.color_space, C1.illuminant)
        self.assertIn(c1_key, m1.colorimetry)
        self.assertEqual(C1, m1.colorimetry[c1_key])


if __name__ == '__main__':
    unittest.main()
