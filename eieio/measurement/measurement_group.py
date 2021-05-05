# -*- coding: utf-8 -*-
"""
Measurement group structure and I/O
================================

Defines the :class:`eieio.measurement.Group` class handling directories full of
*IES TM-27-14*-compliant spectral data XML files: saving, loading, fetching, storing, and
updating.

"""

import os
import re
from json import dumps, loads
from enum import Enum
from datetime import datetime
from pathlib import Path

import toml

from colour.io.tm2714 import Header_IESTM2714, SpectralDistribution_IESTM2714
from colour.colorimetry.datasets.cmfs import MSDS_CMFS_STANDARD_OBSERVER
from colour.models.common import COLOURSPACE_MODELS
from colour.colorimetry.datasets.illuminants.chromaticity_coordinates import CCS_ILLUMINANTS
from eieio.measurement.measurement import Measurement
from eieio.measurement.colorimetry import Colorimetry_IESTM2714
from utilities.english import oxford_join

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Group'
]


class Group(object):
    """
    Manages a collection of related spectral and/or colorimetric measurements

    Attributes
    name : str
        name for this set of collections of measurements
    collections : dict
        lists of filenames stored in a dict, where the key is the directory where the measurements are found
    """

    def __init__(self, group_file):
        """

        Parameters
        ----------
        group_file : str or Path
            path to a TOML file identifying a group and defining groups of measurements
        """
        with open(group_file, mode='r') as f:
            contents = toml.loads(f.read())
            if 'id' in contents and 'name' in contents['id']:
                self._name = contents['id']['name']
            else:
                raise KeyError("Measurement group file must have an 'id' section with a 'name' attribute")
            self._collections = {}
            collection_re = re.compile(r'collections_c\d+')
            for key in contents.keys():
                if collection_re.match(key):
                    measurements = {}
                    dir_ = contents[key]['dir']
                    files = contents[key]['files']
                    for file_ in files:
                        measurement = Measurement()
                        measurement.path = str(Path(dir_, file_))
                        measurement.read()
                        measurements[file_] = measurement
                    self.collections[dir_] = measurements

    def __eq__(self, other):
        if isinstance(other, Group) and self.name == other.name:
            if len(self.collections) == len(other.collections):
                for dir_ in self.collections.keys():
                    if dir_ not in other.collections.keys():
                        return False
                    if len(self.collections[dir_]) != len(other.collections[dir_]):
                        return False
                    for measurements, other_measurements in zip(self.collections[dir_], other.collections[dir_]):
                        if measurements != other_measurements:
                            return False
        return True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def collections(self):
        """

        Returns the dict mapping canonicalized directory paths to sequences of (filename, measurement) pairs
        -------

        """
        return self._collections

    def save_group(self, path):
        """

        Parameters
        ----------
        path : str or Path

        Returns
        -------

        """
        top_level = dict()
        top_level['id'] = {'name': self.name}
        coll_ix = 0
        for dir_, filenames_and_measurements in self.collections.items():
            collection_name = f"collections_c{coll_ix}"
            collection = {'dir': dir_, 'files': filenames_and_measurements.keys()}
            top_level[collection_name] = collection
            coll_ix = coll_ix + 1
        with open(path, 'w') as f:
            print(toml.dumps(top_level), file=f)

    def insert_measurement_from_file(self, path, replace_ok=False):
        """

        Parameters
        ----------
        path : str or Path
            file from which measurement will be loaded
        replace_ok : bool
            if false and there is a measurement from the same file, raise ValueError
        """
        m = Measurement()
        m.path = path
        m.read()
        dir_ = Path(path).parents[0]
        file_ = Path(path).name
        if dir_ in self.collections:
            if file_ in self.collections[dir] and not replace_ok:
                raise ValueError(f"Attempted insertion of measurement from file {path} in a "
                                 "measurement group where a measurement from that file is "
                                 "already present")
            self.collections[dir_][file_] = m

    def insert_measureents_from_dir(self, dir_, replace_ok=False):
        spectral_paths = Path(dir_).glob('*.spdx')
        for path_ in spectral_paths:
            self.insert_measurement_from_file(path_, replace_ok=replace_ok)

    def insert_measurements_from_group(self, path, replace_ok=False):
        """

        Parameters
        ----------
        path : str or Path
            location of a TOML file defining a measurement group
        replace_ok: bool
            if false and there is a measurement from the same file, raise ValueError
        """
        other = Group(path)
        for collection in other.collections.values():
            for dir_, files in collection:
                for file_ in files:
                    self.insert_measurement_from_file(Path(dir_, file_), replace_ok=replace_ok)

    # def add_colorimetry(self, uid, meter_name, colorimetry, **kwargs):
        # key = (uid, meter_name)
        # if key not in self._sds:
        #     header = Header_IESTM2714(comments=Session.colorimetry_as_json(colorimetry))
        #     sd = SpectralDistribution_IESTM2714(header=header, **kwargs)
        # else:
        #     sd = self._sds[key]
        #     session_colorimetry = Group.colorimetry_from_json(sd.header.comments)
        #     session_colorimetry.append(colorimetry)
        #     sd.header.comments = Group.colorimetry_as_json(session_colorimetry)
        # self._sds[key] = sd

    # def load(self):
    #     for _, _, files in os.walk(self.measurement_dir):
    #         files.sort()
    #         for file in files:
    #             if Path(file).suffix == SPECTRAL_SUFFIX:
    #                 measurement_path = str(Path(self.measurement_dir, file))
    #                 sd = SpectralDistribution_IESTM2714(measurement_path)
    #                 sd.read()
    #                 self.add_spectral_measurement(sd)
    #             elif Path(file).suffix == COLORIMETRIC_SUFFIX:
    #                 tcm = Colorimetry_IESTM2714(file)
    #                 self.add_tristimulus_colorimetry_measurement(tcm)
    #
    # def save(self):
    #     for key in self._dirty_keys:
    #         sd = self._sds[key]
    #         if not sd:
    #             raise RuntimeError(f"could not find spectral distribution with path {key}")
    #         print(f"writing spectral distribution to {sd.path}")
    #         sd.write()
    #     self._dirty_keys = set()
    #     for key in self._dirty_tscs_keys:
    #         tsc = self._tscs[key]
    #         if not tsc:
    #             raise RuntimeError(f"could not find tristimulus colorimetry with path {key}")
    #         print(f"writing tristimulus colorimetry to {tsc.path}")
    #         tsc.write()
    #     self._dirty_tscs_keys = set()
    #
    # def add_timestamped_measurement(self, measurement, dict_, key_set):
    #     addition_timestamp = self.timestamp()
    #     # There shouldn't already be a directory but just in case, remove any before
    #     # setting up this spectral_measurement for later saving to the spectral_measurement session_dir.
    #     measurement.path = str(Path(self.measurement_dir, Path(measurement.path).name))
    #     dict_[measurement.path] = measurement
    #     key_set.add(measurement.path)
    #
    # def add_spectral_measurement(self, measurement):
    #     self.add_timestamped_measurement(measurement, self._sds, self._dirty_keys)
    #
    # def add_tristimulus_colorimetry_measurement(self, measurement):
    #     self.add_timestamped_measurement(measurement, self._tscs, self._dirty_tscs_keys)
    #
    # def contains_unsaved_measurements(self):
    #     return len(self._dirty_keys) > 0 or len(self._dirty_tscs_keys) > 0
