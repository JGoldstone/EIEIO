# -*- coding: utf-8 -*-
"""
An extended IES TM 2714 spectral distribution carrying tristimulus colorimetry as well.
================================

Defines the :class:`eieio.measurement.Measurement` class by subclassing :class:`colour.io.tm2714`


"""


from colour.io.tm2714 import SpectralDistribution_IESTM2714

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Measurement'
]


class Measurement(SpectralDistribution_IESTM2714):
    def __init__(self, **kwargs):
        super(Measurement, self).__init__(**kwargs)
        self._colorimetry = []

    def __eq__(self, other):
        mappings = getattr(self, 'mapping')
        if not mappings:
            raise RuntimeError("can't compare Measurements for equality: no mappings")
        other_mappings = getattr(other, 'mapping')
        if not other_mappings:
            raise RuntimeError("can't compare Measurements for equality: no mappings in other")
        if set(mappings.keys()) != set(other_mappings.keys()):
            return False
        if mappings['element'] != other_mappings['elememnt']:
            return False
        for mapping in [mappings['elements'], mappings['data']]:
            for spec in mapping:
                if not getattr(self, spec.attribute):
                    return False
                if not getattr(other, spec.attribute):
                    return False
                if not getattr(self, spec.attribute) == getattr(other, spec.attribute):
                    return False
        return True

    def colorimetry(self, observer=None, color_space=None, illuminant=None):
        """

        Parameters
        ----------
        observer : str
            filtering parameter matching observer names used in :class:`eieio.measurement.colorimetry`.
            Defaults to None; if so defaulted, acts as a wildcard.
        color_space
            filtering parameter matching color space names used in :class:`eieio.measurement.colorimetry`
            Defaults to None; if so defaulted, acts as a wildcard.
        illuminant
            filtering parameter matching illuminant names used in :class:`eieio.measurement.colorimetry`
            Defaults to None; if so defaulted, acts as a wildcard.

        Returns
        -------
        Colorimetry either found in existing colorimetry, or converted directly
        or indirectly from what we have.

        """
        pass

