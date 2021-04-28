# -*- coding: utf-8 -*-
"""
Unit tests for the spectral_measurement session class
================================

Test the :class:`spectral_measurement.session.MeasurementSession` class.

"""

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
]

import os
import unittest
import eieio.measurement.session as ms
from datetime import datetime
from pathlib import Path
from colour.io.tm2714 import SpectralDistribution_IESTM2714

EIEIO_PATH = f"./{ms.MeasurementSession.EIEIO_CONFIG}"
EIEIO_DATA_DIR = '../../data'
EIEIO_SAMPLE_IES_TM2714_SD_NAME = 'sample_spectral_radiance_measurement.xml'


def write_blank_eieio_config():
    with open(EIEIO_PATH, 'w') as f:
        print('[measurements]', file=f)


def write_test_eieio_config(base_dir_path=None, dir_name=None):
    base_dir_path = base_dir_path if base_dir_path else 'foo'
    dir_name = dir_name if dir_name else 'bar'
    with open(EIEIO_PATH, 'w') as f:
        print("top_level = 'a thing'", file=f)
        print('[measurements]', file=f)
        print(f"base_dir_path = '{base_dir_path}'", file=f)
        print(f"dir_name = '{dir_name}'", file=f)


def is_parseable_date(str_):
    try:
        datetime.strptime(str_, ms.MeasurementSession.TIMESTAMP_FORMAT)
    except ValueError:
        return False
    return True


class MyTestCase(unittest.TestCase):
    def test_EIEIO_MISSING(self):
        Path(EIEIO_PATH).unlink(missing_ok=True)
        eieio_dict = ms.MeasurementSession.load_eieio_defaults()
        self.assertEqual(eieio_dict['measurements']['base_dir_path'], '/var/tmp')

    def test_check_path_is_writable_nonexistent_dir(self):
        self.assertRaises(FileNotFoundError, ms.MeasurementSession.check_path_is_writable_dir, '/foo',
                          "a directory (nonexistent for this test")

    def test_check_path_is_writable_plain_file(self):
        try:
            write_test_eieio_config("/Users/share/data")
            self.assertRaises(FileExistsError, ms.MeasurementSession.check_path_is_writable_dir, EIEIO_PATH,
                              "a plain file (for which we DO have write permission")
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_check_path_is_writable_no_write_permission(self):
        self.assertRaises(ProcessLookupError, ms.MeasurementSession.check_path_is_writable_dir, '/etc',
                          "a directory for which we lack write permission")

    def test_default_path_from_eieio_from_component(self):
        try:
            write_test_eieio_config("/Users/share/data")
            p = ms.MeasurementSession.default_path_component_from_eieio("/foo/bar", '/tmp/default_default',
                                                                        'measurements.base_dir_path')
            self.assertEqual(p, "/foo/bar")
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_EIEIO_default_path_from_eieio_from_eieio_TL_bad(self):
        try:
            write_test_eieio_config(None, None)
            p = ms.MeasurementSession.default_path_component_from_eieio(None, '/tmp/default_default', 'x_top_level')
            self.assertEqual(p, "/tmp/default_default")
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_EIEIO_default_path_from_eieio_from_eieio_TL_good(self):
        try:
            write_test_eieio_config("/var/tmp/data", None)
            p = ms.MeasurementSession.default_path_component_from_eieio(None, '/tmp/default_default', 'top_level')
            self.assertEqual(p, 'a thing')
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_EIEIO_default_path_from_eieio_from_eieio_bad(self):
        try:
            write_test_eieio_config(None, None)
            p = ms.MeasurementSession.default_path_component_from_eieio(None, '/tmp/default_default',
                                                                        'measurements.x_base_dir_path')
            self.assertEqual(p, "/tmp/default_default")
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_EIEIO_default_path_from_eieio_from_eieio_good(self):
        try:
            write_test_eieio_config("/var/tmp/data", None)
            p = ms.MeasurementSession.default_path_component_from_eieio(None, '/tmp/default_default',
                                                                        'measurements.base_dir_path')
            self.assertEqual(p, "/var/tmp/data")
        finally:
            Path(EIEIO_PATH).unlink(missing_ok=True)

    def test_session_ctor(self):
        session = ms.MeasurementSession('/var/tmp')
        p = Path(session.measurement_dir)
        self.assertEqual(p.parent, Path('/var/tmp'))
        self.assertTrue(is_parseable_date(p.name))
        self.assertTrue(p.exists())
        self.assertEqual(len(session._sds), 0)
        self.assertEqual(len(session._dirty_sds_keys), 0)
        self.assertEqual(len(session._tscs), 0)
        self.assertEqual(len(session._dirty_tscs_keys), 0)

    def test_spectral_loading(self):
        session = ms.MeasurementSession('/var/tmp')
        sd_path = Path(EIEIO_DATA_DIR, EIEIO_SAMPLE_IES_TM2714_SD_NAME)
        sd = SpectralDistribution_IESTM2714(str(sd_path)).read()
        session.add_spectral_measurement(sd)
        self.assertEqual(len(session._sds), 1)
        self.assertEqual(len(session._dirty_sds_keys), 1)
        self.assertEqual(len(session._tscs), 0)
        self.assertEqual(len(session._dirty_tscs_keys), 0)

    def test_spectral_saving(self):
        session = ms.MeasurementSession('/var/tmp')
        sd_path = Path(EIEIO_DATA_DIR, EIEIO_SAMPLE_IES_TM2714_SD_NAME)
        sd = SpectralDistribution_IESTM2714(str(sd_path)).read()
        session.add_spectral_measurement(sd)
        _, _, files = next(os.walk(session.measurement_dir))
        print(f"len of files is {len(files)}")
        for f in files:
            print(f"file is `{f}'")
        num_pre_save_files = len(files)
        session.save()
        self.assertEqual(len(session._sds), 1)
        self.assertEqual(len(session._dirty_sds_keys), 0)
        _, _, files = next(os.walk(session.measurement_dir))
        for f in files:
            print(f"file is `{f}")
        num_post_save_files = len(files)
        self.assertEqual(num_post_save_files, num_pre_save_files + 1)


if __name__ == '__main__':
    unittest.main()
