# -*- coding: utf-8 -*-
"""
Concrete class implementing support for Sekonic colorimeters and spectoradiometers
===================

Implement support for the Sekonic C-800 as an offline colorimeter.

"""

from enum import Enum
import re
import subprocess

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Sekonic'
]

WPD_JS = 'wpd.js'

class Model(Enum):
    C700R = 0
    C800 = 1
    C7000 = 2


class MeasuringMode(Enum):
    AMBIENT = 0


class Domain(Enum):
    DIGITAL = 0
    FILM = 1


class CCT(Enum):

class Capability(object):
    """
    Models a capability of a Sekonic meter. Capabilities are provided in two
    different ways: natively (i.e. one can obtain the value directly, by
    reading the output of the device) or through derivation. For example,
    the C-7000 meter directly provides a spectral product distribution. The
    C-800 meter indirectly provides a spectral product distribution by an
    analysis of a downloaded PNG file of a graph of the spectral power
    distribution that the C-800 will provide.
    """

    def __init__(self, name, regex_pattern, native_meter_support, derived_meter_support):
        """

        Parameters
        ----------
        name : str
            name of the capability, e.g. 'spd'
        regex_pattern : str
            regex pattern by which the capability can be recognized
        native_meter_support : sequence of Model
            sequence of models where the capability is natively available
        derived_meter_support : sequence of Model
            sequence of models where the capability is not natively available but can be derived
        """
        self._name = name
        self._regex_pattern = regex_pattern
        self._native_meter_support = native_meter_support
        self._derived_meter_support = derived_meter_support




class Sekonic(object):
    @classmethod
    def load_capabilities(cls):
        cls._capabilities = [
            Capability()
        ]

    def __init__(self, model, csv_path):
        """
        Models a Sekonic C-800 colorimeter, with the data delivered offline as CSV files.

        Sessions are not intended to be saved; they might be useful as part of a database
        loader someday, but for now they are handy ways to group measurements for presentation
        to Dash apps, or whatever.

        Attributes
        date_saved : str
            colour.colorimetry.spectrum.SpectralDistribution objects, keyed by filename
        title : str
            name of tristimulus color space.
        measuring_mode : str
            one of 'ambient', ... # TODO find the set of values
        mode: str
            one of ''Digital' or 'Film'
        cct: float
            correlated color temperature in 'Digital Mode'; photograpjic color temperature in 'Film' mode.
        delta_uv: float
            brochure says "Displays deviance from the black-body radiation"
        illuminance_exp_1:
        illuminance_exp_2:
        target_cct
        lb_index:
            brochure says "Displays the LB (Light Balancing) corrected value in LB index"
        lb_camera_filter
            brochure says "Displays the LB corrected value in the compensation filter name. The filter brad is selected in the Measuring screens and Setting Mode"
        lb_lighting_filter
        cc_index
        cc_camera_filter
        cc_lighting_filter
        cri_average: float
            brochure says "Displays the average value of CRI (Color Rendering Index) R1 to R8
        cri_samples: float
            CRIs numbered 1 to 15 inclusive

        cri_rs
        tm_30_rf
        tm_30_rg
        sslt: float
            Spectral Similarity Index (Tungsten)
        ssld: float
            Spectral Similarity Index (Daylight)
        ssl1: float
            Spectral Similarity Index (1 ?)
        ssl2: float
            Spectral Similarity Index (2 ?)
        tlci : float
            Television Lighting Consistency Index (-2012: EBU R 137, rev 2.0)
        tlmf : float
            Television Luminaire Matching Factor (-2013: EBU R 137, rev 2.0)
        x : float
            CIE tristimulus colorimetry x coordinate
        y : float
            CIE tristimulus colorimetry y coordinate
        hue
        saturation
        """
        self._possible_capabilities = None
        self._capabilities = None

    def load(self, path):
        rows = csv.read(path)
        # deal with date saved line here
        # deal with title here
        ix = 0
        row_pattern = r'^(\w*),(\w*)$'
        row_regex = re.compile(row_pattern)
        for i, row in enumerate(rows):
            line = i + 1
            if not row and line != 3:
                raise RuntimeError(f"line {line}: line was blank, but only line 3 is blank in Sekonic output.")
            row_match = re.match(row_regex, row)
            if not row_match:
                raise RuntimeError(f"line {line}: line `{row}' doesn't look like a Sekonic key, value pair")
            key = row_match.group(1)
            value = row_match.group(2)
            for capability in self._possible_capabilities[ix:]:
                if capability.match(key):
                    self._capabilities[capability.name] = value

    @classmethod
    def clean_spd_grid_image(cls):
        pass

    def sd_from_image(self, measured_spd_image):
        grid = Sekonic.clean_spd_grid_image
        img = oiio.load(measured_spd_image)
        img.add(grid)
        try:
            tmp_file = get_scratch_file()
            img.write(tmp_file)
            wpd_
            p = subprocess.Popen('node', '')
        finally:
            if tmp_file:
                remove tmp_file



