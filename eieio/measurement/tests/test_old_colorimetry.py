import unittest
from colour.io.tm2714 import Header_IESTM2714
from eieio.measurement.old_colorimetry import ColxColorimetry, Colorimetry_IESTM2714, Origin

class colorimetry_tests(unittest.TestCase):
    def test_normal_CIE_XYZ_Colorimetry(self):
        c = Colorimetry('2º', 'CIE XYZ', [0.2, 0.3, 0.4])
        self.assertEqual(c.observer, 'CIE 1931 2 Degree Standard Observer')
        self.assertEqual(c.model_name, 'CIE XYZ')
        self.assertEqual(c.component_labels[0], 'X')
        self.assertEqual(c.component_labels[1], 'Y')
        self.assertEqual(c.component_labels[2], 'Z')
        self.assertEqual(c.component_values[0], 0.2)
        self.assertEqual(c.component_values[1], 0.3)
        self.assertEqual(c.component_values[2], 0.4)
        self.assertEqual(c.reference_white, None)

    def test_normal_CIE_XYZ_IESTM2714_Colorimetry(self):
        c = Colorimetry('2º', 'CIE XYZ', [0.2, 0.3, 0.4])
        h = Header_IESTM2714(manufacturer='foo', catalog_number='bar', description='baz', document_creator='me',
                             unique_identifier='aaa', measurement_equipment='bbb', laboratory='ccc',
                             report_number='ddd', report_date='eee', document_creation_date='today',
                             comments='mot really')
        i = Colorimetry_IESTM2714(header=h, colorimetry=c, origin=Origin.MEASURED)
        self.assertEqual(i.path, None)

if __name__ == '__main__':
    unittest.main()
