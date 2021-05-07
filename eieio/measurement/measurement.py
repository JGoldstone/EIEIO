# -*- coding: utf-8 -*-
"""
An extended IES TM 2714 spectral distribution carrying tristimulus colorimetry as well.
================================

Defines the :class:`eieio.measurement.Measurement` class by subclassing :class:`colour.io.tm2714`


"""

import json
from colour.io.tm2714 import SpectralDistribution_IESTM2714
from eieio.measurement.colorimetry import Colorimetry


__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Measurement'
]

# TODO make this list comprehensive
ILLUMINANT_INSENSITIVE_MODELS = ('CIE XYZ', 'CIE xyY', 'CIE UCS', 'IPT', 'HDR IPT')


class Measurement(SpectralDistribution_IESTM2714):
    def __init__(self, **kwargs):
        super(Measurement, self).__init__(**kwargs)
        comments = self.header.comments
        self._colorimetry = None
        self.colorimetry = Measurement.extract_colorimetry_from_json(comments) if comments else {}

    def write(self):
        self.header.comments = self.extra_metadata_as_json()
        if not self.values.any():
            min_lambda = 380
            max_lambda = 780
            num_lambdas = 1 + max_lambda - min_lambda
            self.values = [1/num_lambdas] * num_lambdas
            self.wavelengths = list(range(min_lambda, 1 + max_lambda))
        if not self.bandwidth_FWHM:
            self.bandwidth_FWHM = 10  # arbitrary, just can't be N/A or tm2714 reader explodes
        super(Measurement, self).write()

    def read(self):
        super(Measurement, self).read()
        if self.header.comments and self.header.comments != 'N/A':
            self.colorimetry = Measurement.extract_colorimetry_from_json(self.header.comments)

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

    def comma_keyed_colorimetry(self):
        comma_keyed = {}
        for c in self._colorimetry.values():
            key = ','.join([c.observer, c.color_space, c.illuminant])
            comma_keyed[key] = (c.values, c.origin)
        return comma_keyed

    def extra_metadata_as_json(self):
        return json.dumps({'eieio': {'colorimetry': self.comma_keyed_colorimetry()}})

    @property
    def colorimetry(self):
        return self._colorimetry

    @colorimetry.setter
    def colorimetry(self, value):
        self._colorimetry = value

    @staticmethod
    def extract_colorimetry_from_json(text):
        extra_md = json.loads(text)
        c = {}
        for comma_key, values_and_derivation in extra_md['eieio']['colorimetry'].items():
            observer, color_space, illuminant = comma_key.split(',')
            values, derivation = values_and_derivation
            c[(observer, color_space, illuminant)] = Colorimetry(observer, color_space, illuminant, values, derivation)
        return c

    def insert_colorimetry(self, c: Colorimetry, replace_ok=False):
        key = (c.observer, c.color_space, c.illuminant)
        if key in self.colorimetry and not replace_ok:
            raise ValueError(f"colorimetric value with color space `{c.color_space}', "
                             f"observer `{c.observer}', and illuminant `{c.illuminant}' "
                             "is already present in measurement.")
        self.colorimetry[key] = c

    def remove_colorimemtry(self, c: Colorimetry, missing_ok=False):
        key = (c.observer, c.color_space, c.illuminant)
        if key not in self.colorimetry and not missing_ok:
            raise ValueError(f"colorimetric value with color space `{c.color_space}', "
                             f"observer `{c.observer}', and illuminant `{c.illuminant}' "
                             "is not present in measurement, and therefore cannot "
                             "be removed")
        del self.colorimetry[key]

    def retrieve_colorimetry(self, color_space, observer, illuminant):
        """

        Parameters
        ----------
        color_space
            filtering parameter matching color space names used in :class:`eieio.measurement.colorimetry`.
        observer : str
            filtering parameter matching observer names used in :class:`eieio.measurement.colorimetry`.
            Defaults to None; if so defaulted, acts as a wildcard
        illuminant
            filtering parameter matching illuminant names used in :class:`eieio.measurement.colorimetry`

        Returns
        -------
        Colorimetry either found in existing colorimetry, or converted directly
        or indirectly from what we have.

        """
        if not color_space:
            raise ValueError("Can't derive colorimetry if no color space is specified")
        for c in self.colorimetry:
            if c.color_space == color_space and c.observer == observer:
                if color_space in ILLUMINANT_INSENSITIVE_MODELS:
                    return c
                elif c.illuminant == illuminant:
                    return c
        # TODO derive the requested colorspace from something we already have
