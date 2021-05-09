# -*- coding: utf-8 -*-
"""
Measurement group structure and I/O
================================

Defines the :class:`eieio.measurement.Group` class handling directories full of
*IES TM-27-14*-compliant spectral data XML files: saving, loading, fetching, storing, and
updating.

"""

import re
from pathlib import Path

import toml

from eieio.measurement.measurement import Measurement

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

    def __init__(self, group_file, missing_ok=False):
        """

        Parameters
        ----------
        group_file : str or Path
            path to a TOML file identifying a group and defining groups of measurements
        """
        try:
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
        except FileNotFoundError:
            if missing_ok:  # getting ready to create it, but not yet
                self.name = Path(group_file).name
                self._collections = {}

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
        m.path = str(path)
        m.read()
        dir_ = str(Path(path).parents[0])
        file_ = str(Path(path).name)
        if dir_ in self.collections:
            if file_ in self.collections[dir_] and not replace_ok:
                raise ValueError(f"Attempted insertion of measurement from file {path} in a "
                                 "measurement group where a measurement from that file is "
                                 "already present")
            self.collections[dir_][file_] = m
        else:
            self.collections[dir_] = {file_: m}

    def remove_measurement_from_file(self, path, missing_ok=False):
        dir_ = Path(path).parents[0]
        name = Path(path).name
        if dir_ not in self.collections:
            if not missing_ok:
                raise ValueError(f"Attempted removal of measurement from file {path} "
                                 "from group, but no measurement from that file was found")
        else:
            if name not in self.collections[dir_]:
                if not missing_ok:
                    raise ValueError(f"Attempted removal of measurement from file {path} "
                                     "from group, but no measurement from that file was found")
            else:
                del self.collections[dir_][name]

    def insert_measurements_from_dir(self, dir_, replace_ok=False):
        spectral_paths = Path(dir_).glob('*.spdx')
        for path_ in spectral_paths:
            self.insert_measurement_from_file(path_, replace_ok=replace_ok)

    def remove_measurements_from_dir(self, dir_, missing_ok=False):
        if dir_ not in self.collections:
            if not missing_ok:
                raise ValueError(f"Attempted removal of measurements from directory {dir_} "
                                 "from group, but no measurements from that directory were found")
        else:
            del self.collections[dir_]

    def insert_measuremments_from_group(self, other, replace_ok=False):
        for dir_ in other.collections:
            for file, measurement in other.collections[dir_].items():
                if dir_ in self.collections:
                    if file in self.collections[dir_] and not replace_ok:
                        raise ValueError(f"Attempted insertion of measurement from group in a "
                                         "measurement group where that measurement was "
                                         "already present")
                    self.collections[dir_][file] = measurement
                else:
                    self.collections[dir_] = {file: measurement}

    def remove_measurements_from_group(self, other, missing_ok=False):
        for dir_ in other.collections:
            if dir_ in self.collections:
                for file in other.collections[dir_].keys():
                    if file in self.collections[dir_]:
                        del self.collections[dir_][file]
                    else:
                        if not missing_ok:
                            raise ValueError("Attempted removal of measurement from group in a "
                                             "measurement group where that measurement was not "
                                             "present")
            else:
                if not missing_ok:
                    raise ValueError("Attempted removal of measurement from group in a "
                                     "measurement group where that measurement was not "
                                     "present")

    def insert_measurements_from_group_file(self, path, replace_ok=False):
        """

        Parameters
        ----------
        path : str or Path
            location of a TOML file defining a measurement group
        replace_ok: bool
            if false and there is a measurement from the same file, raise ValueError
        """
        self.insert_measuremments_from_group(Group(path), replace_ok=replace_ok)

    def remove_measurements_from_group_file(self, path, missing_ok=False):
        self.remove_measurements_from_group(Group(path), missing_ok=missing_ok)

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
