# -*- coding: utf-8 -*-
"""
Stand-in tristimulus colorimetry class
================================

Defines the :class:`measurement.session.TristimulusColorimetryMeasurement` class handling
directories full of TOML files with colorimetric data.

"""

from pathlib import Path
import toml

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'TristimulusColorimetryMeasurement'
]


class TristimulusColorimetryMeasurement(object):

    def __init__(self, path, colorspace=None, values=None):
        self.path = path
        if path:
            if Path(path).exists():
                stored = toml.load(path)
                self.colorspace = colorspace if colorspace else stored['attributes']['colorspace']
                self.values = values if values else stored['payload']['values']
            else:
                raise FileNotFoundError("could not find tristimulus colorimetry file (.colx) at {path}")
        else:
            self.colorspace = colorspace if colorspace else None
            self.values = values if values else None
