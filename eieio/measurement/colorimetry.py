# -*- coding: utf-8 -*-
"""
Tristimulus colorimetry
================================

Defines the :class:`eieio.measurement.Colorimetry` class, holding different colorimetric
views of an actual or hypothetical spectral or colorimetric measurement. All supported
colorimetric conversions in the Colour package can be used to switch between tristimulus
color spaces, to a reasonable extent. (Unreasonable means you don't have the original
spectral distribution and you want to convert between color spaces associated with
different observers.

The tristimulus values are linearly represented.
"""

from colour.colorimetry.datasets.cmfs import MSDS_CMFS_STANDARD_OBSERVER
from colour.models.common import COLOURSPACE_MODELS
from colour.colorimetry.datasets.illuminants.sds import SDS_ILLUMINANTS
from utilities.english import oxford_join

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Colorimetry'
]

MEASUREMENT_ORIGINS = ('unknown', 'measured', 'derived', 'synthesized', 'manual_input')


class Colorimetry(object):
    """
    Package together observer, color space name, values and optionally an identified origin for the measurement

    Attributes:
    observer : str
        name of an observer from colour.colorimetry.datasets.cmfs.MSDS_CMFS_STANDARD_OBSERVER
    colorspace : str
        name of a colorspace from colour.models.common.COLOURSPACE_MODELS
    illuminant : str
        name of an illuminant from color.colorimetry.datqsets.illuminants.chromaticity_coordinates.CCS_ILLUMINANTS
    values : sequence
        triplet of tristimulus values
    origin : str
        one of 'unknown', 'measured', 'derived', 'synthesized' or 'manual_input'
    """
    def __init__(self, observer, color_space, illuminant, values, origin=None):
        self._observer = None
        self._color_space = None
        self._illuminant = None
        self.observer = observer
        self.color_space = color_space
        self.illuminant = illuminant
        observer = observer.replace('_', ' ').lower()  # TODO clean this up
        color_space = color_space.replace('_' ,' ').lower()
        illuminant = illuminant.replace('_', ' ').lower()
        # if observer not in [key.lower() for key in MSDS_CMFS_STANDARD_OBSERVER.keys()]:
        #     raise ValueError(f"'observer' argument to Colorimetry ctor must be one of "
        #                      f"{oxford_join(list(MSDS_CMFS_STANDARD_OBSERVER.keys()), 'or')}")
        # self._observer = None
        # self.observer = observer
        # if color_space not in [model.lower() for model in COLOURSPACE_MODELS]:
        #     raise ValueError(f"'color_space' argument to Colorimetry ctor must be one of "
        #                      f"{oxford_join(COLOURSPACE_MODELS, 'or')}")
        # self._color_space = None
        # self.color_space = color_space
        # if illuminant not in [illum.lower() for illum in SDS_ILLUMINANTS.keys()]:
        #     raise ValueError(f"'illuminant' argument to Colorimetry ctor must be one of "
        #                      f"{oxford_join(list(SDS_ILLUMINANTS.keys()), 'or')}")
        # self._illuminant = None
        # self.illuminant = illuminant
        if len(values) != 3:
            raise ValueError("'values' argument to Colorimetry ctor must have exactly "
                             "three elements")
        self._values = None
        self.values = values
        if origin not in MEASUREMENT_ORIGINS:
            raise ValueError(f"'origin' argument to Colorimetry ctor must be one of "
                             f"{oxford_join(MEASUREMENT_ORIGINS, 'or')}")
        self._origin = None
        self.origin = origin

    def __str__(self):
        pretty_observer = ''
        if self.observer:
            if self.observer.lower() in (o.lower() for o in ('CIE 1931 2 Degree Standard Observer', 'cie_2_1931')):
                pretty_observer = ' 2º'
            elif self.observer.lower() in (o.lower() for o in ('CIE 1964 10 Degree Standard Observer', 'cie_10_1964')):
                pretty_observer = ' 10º'
            elif self.observer.lower() == 'CIE 2012 2 Degree Standard Observer'.lower():
                pretty_observer = ' 2º (2012)'
            elif self.observer.lower() == 'CIE 2012 10 Degree Standard Observer'.lower():
                pretty_observer = ' 10º (2012)'
        pretty_illuminant = ''
        if self.illuminant:
            if self.color_space.lower() not in (cs.lower() for cs in ('CIE_XYZ', 'CIE_xyY', 'RxRyRz', 'RGB',
                                                                      'Lv_xy', 'Y_xy', 'Lv_T_duv',
                                                                      'Dominant_wavelength_and_excitation_purity')):
                pretty_illuminant = f" / {self.illuminant}" if pretty_observer else f" {self.illuminant}"
        pretty_origin = f" {self.origin}" if self.origin and self.origin != 'measured' else ''
        result = f"{self.color_space}"
        if pretty_observer or pretty_illuminant or pretty_origin:
            result = f"{result} ({pretty_observer}{pretty_illuminant} )"
        if self.origin and self.origin != 'measured':
            result = f"{result} [{self.origin}]"
        result = f"{result}:"
        for value in self.values:
            result = f"{result} {value}"
        return result
        # CIE LAB (2º, D65): 85.2 19.0 47.2

    @property
    def observer(self):
        return self._observer

    @observer.setter
    def observer(self, value):
        new_value = value.replace('_', ' ').lower()
        for candidate_observer in list(MSDS_CMFS_STANDARD_OBSERVER.keys()):
            if new_value == candidate_observer.lower():
                self._observer = candidate_observer
                return
        raise ValueError(f"Attempt to set Colorimetry observer attribute to `{value}', "
                         f"an unsupported observer. Supported observers are "
                         f"{oxford_join(list(MSDS_CMFS_STANDARD_OBSERVER.keys()), 'or')}.")

    @property
    def color_space(self):
        return self._color_space

    @color_space.setter
    def color_space(self, value):
        new_value = value.replace('_', ' ').lower()
        for candidate_space in COLOURSPACE_MODELS:
            if new_value == candidate_space.lower():
                self._color_space = candidate_space
                return
        raise ValueError(f"Attempt to set Colorimetry color_space attribute to `{value}', "
                         f"an unsupported color space. Supported color spaces are "
                         f"{oxford_join(COLOURSPACE_MODELS, 'or')}.")

    @property
    def illuminant(self):
        return self._illuminant

    @illuminant.setter
    def illuminant(self, value):
        new_value = value.replace('_', ' ').lower()
        for candidate_illuminant in SDS_ILLUMINANTS:
            if new_value == candidate_illuminant.lower():
                self._illuminant = candidate_illuminant
                return
        raise ValueError(f"Attempt to set Colorimetry illuminant to `{value}', "
                         f"an unsupported illuminant. Supported illuminants are "
                         f"{oxford_join(SDS_ILLUMINANTS, 'or')}.")

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, value):
        if not value:
            raise ValueError("tristimulus values cannot be set to 'None'")
        if len(value) != 3:
            raise ValueError('Tristimulus colorimetry must be a triplet of values')
        self._values = value

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        if value not in MEASUREMENT_ORIGINS:
            raise ValueError(f"derivation must be one of {oxford_join(MEASUREMENT_ORIGINS, 'or')}.")
        self._origin = value

    def __eq__(self, other):
        return (other.observer == self.observer
                and other.color_space == self.color_space
                and other.illuminant == self.illuminant
                and other.values == self.values
                and other.origin == self.origin)
