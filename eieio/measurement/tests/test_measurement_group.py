# -*- coding: utf-8 -*-
"""
Unit tests for measurement groupd class
================================

Test the :class:`spectral_measurement.session.Session` class.

"""

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
]


from tempfile import TemporaryDirectory, NamedTemporaryFile
import unittest
from pathlib import Path

import numpy as np

from colour.io.tm2714 import SpectralDistribution_IESTM2714
from eieio.measurement.measurement import Measurement
from eieio.measurement.measurement_group import Group


def make_meas_seq(seq_dir, min_seq_num, max_seq_num):
    for i in range(min_seq_num, max_seq_num+1):
        wavelengths = range(380, 780, 10)
        lerp_factor = (i-min_seq_num)/(max_seq_num-min_seq_num)
        values = np.linspace(lerp_factor, 1-lerp_factor, len(wavelengths))
        m = SpectralDistribution_IESTM2714(description='foo',
                                           document_creator='bar',
                                           document_creation_data='baz',
                                           spectral_quantity='radiance',
                                           bandwidth_FWHM=1.0)
        m.wavelengths = wavelengths
        m.values = values
        path_ = str(Path(seq_dir, f"sample.{i:04}.spdx"))
        print(f"path_ is `{path_}'", flush=True)
        m.path = path_
        m.write()


def make_group_file(group_dir, group_file_name, group_name, *collections):
    """

    Parameters
    ----------
    group_dir : str or Path
        directory to contain the temporary group file    
    group_file_name : str
        name of group file to be created
    group_name : str
        name in the '[id]' section of the group file
    collections : sequence
        sequence of 3-tuples of directory to contain dummy Measurements, and
        minimum and maximum frame numbers

    Returns
    -------
    group_file : Path
    """
    path_ = Path(group_dir, group_file_name)
    print(f"path_ is {path_}")
    with open(path_, mode='w') as f:
        print('[id]', file=f)
        print(f"name = '{group_name}'", file=f)
        print('', file=f)
        print("dark_key = 'foo'", file=f)
        print('[dark_section]', file=f)
        print("other_dark_key = 'bar'", file=f)
        print('', file=f)
        for i, c in enumerate(collections):
            print(f"[collections_c{i:02}]", file=f)
            dir_, min_, max_ = c
            print(f"dir = '{dir_}'", file=f)
            print('files=[', file=f)
            for j in range(min_, max_):
                print(f"  'sample.{j:04}.spdx',", file=f)
            print(f"  'sample.{j+1:04}.spdx'", file=f)
            print('  ]', file=f)
    return path_


RESOURCE_DIR = './resources'
EXISTING_GROUP_FILE = 'test_mg.toml'


class TestGroup(unittest.TestCase):
    def test_number_of_loaded_collections(self):
        coll_0_min, coll_0_max = [0, 4]
        coll_1_min, coll_1_max = [0, 3]
        with TemporaryDirectory() as group_file_dir:
            with TemporaryDirectory() as seq_0_dir:
                with TemporaryDirectory() as seq_1_dir:
                    make_meas_seq(seq_0_dir, coll_0_min, coll_0_max)
                    make_meas_seq(seq_1_dir, coll_1_min, coll_1_max)
                    fn = make_group_file(group_file_dir, 'test_group.toml', 'grouper',
                                         *[[seq_0_dir, coll_0_min, coll_0_max],
                                           [seq_1_dir, coll_1_min, coll_1_max]])
                    mg = Group(fn)
                    self.assertEqual('grouper', mg.name)
                    # check number of collections is correct
                    self.assertEqual(2, len(mg.collections))
                    # check number of members of each collection is the same
                    self.assertEqual(1 + coll_0_max - coll_0_min, len(mg.collections[seq_0_dir]))
                    self.assertEqual(1 + coll_1_max - coll_1_min, len(mg.collections[seq_1_dir]))
                    # (implicitly) check that dark metadata (sections and keys) are ignored.
                    # check that we can round-trip
                    with NamedTemporaryFile() as round_trip_copy_file:
                        rt_name = round_trip_copy_file.name
                        mg.save_group(rt_name)
                        round_trip_copy = Group(rt_name)
                        self.assertEqual(mg, round_trip_copy)

    # def collections_are_equal(self, c0, c1):
    #     if c0['dir'] != c1['dir']:
    #         return False
    #     c0_files = c0['files']
    #     c1_files = c1['files']
    #     if len(c0_files) != len(c1_files):
    #         return False
    #     if set(c0_files) != set(c1_files):
    #         return False
    #     for f1, f2 in zip(c0_files, c1_files):
    #         if Measurement(f1) != Measurement(f2):
    #             return False
    #     return True


    def test_insert_file_from_unknown_dir(self):
        pass

    def test_insert_file_from_known_dir(self):
        pass

    def test_insert_files_from_dir(self):
        pass

    def test_insert_files_from_group(self):
        # load A, load B, sve to temp, load from temp, load A+B, temp == A+B
        pass

    def test_remove_nonexistent_file_raises(self):
        # load
        pass

    def test_remove_file_from_dir_with_multiple_files(self):
        pass

    def test_remove_file_from_dir_with_only_that_file(self):
        pass

    def test_remove_files_from_dir(self):
        pass

    def test_remove_files_from_group(self):
        pass

    def test_pure_spectra_load(self):
        pass

    def test_pure_colorimetry_loads(self):
        pass

    def test_spectra_and_colorimetry_load(self):
        pass

    def test_synthetic_CIE_XYZ_from_spectra(self):
        pass

    def test_synthetic_xy_from_spectra(self):
        pass

    def test_synthetic_xy_from_XYZ(self):
        pass


if __name__ == '__main__':
    # unittest.main()
    make_group_file('/tmp', 'foo.toml', 'test_group', ['/tmp/foo', 1, 6], ['/tmp/bar', 0, 4])

