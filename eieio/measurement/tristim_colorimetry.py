# -*- coding: utf-8 -*-
"""
Stand-in tristimulus colorimetry class
================================

Defines the :class:`measurement.session.TristimulusColorimetryMeasurement` class handling
directories full of TOML files with colorimetric data.

"""

from pathlib import Path
from colour.colorimetry.tristimulus import sd_to_XYZ
from colour.models.cie_xyy import XYZ_to_xy, XYZ_to_xyY
from colour.utilities.array import tstack
import xml.etree.ElementTree as ET
import toml
from eieio.meter.meter_abstractions import Mode, Quantity

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'TristimulusColorimetryMeasurement'
]

VERSION_EIEIO_COLORIMETRY = '0.1'
NAMESPACE_EIEIO_COLORIMETRY = 'http://www.arri.de/camera'

class TristimulusColorimetryHeader(object):
    def __init__(self, quality='luminance', refl_geo='N/A', trans_geo='0:0', bw_fwhm=25, bw_corr_data=False):
        self.colorimetric_quality = quality
        self.reflection_geometry = refl_geo
        self.transmission_geometry = trans_geo
        self.bandwidth_fwhm = bw_fwhm
        self.bandwidth_corrected_data = bw_corr_data


class TristimulusColorimetryMeasurement(object):

    def __init__(self, path, colorspace=None, values=None):
        self.path = None
        self.tm2714_header = None
        self.tristim_header = None
        self.colorspace_model_name = None
        self.colorspace_data = []

    def add_colorimetry(self, tm2714_header, tristim_header, colorspace_model_name, values):
        self.tristim_header = tristim_header
        self.colorspace_model_name = colorspace_model_name
        self.colorspace_data = values

    def add_from_XYZ(self, tm2714_header, XYZ, models, **kwargs):
        models_to_conversion_functions = {
            'cie xyy': (XYZ_to_xyY, 'CIE xyY'),
            'cie xy': (XYZ_to_xy, 'CIE xy')
        }
        for model in models:
            if model.lower not in models_to_conversion_functions:
                raise RuntimeError(f"colorspace `{model}' is not supported: supported colorspaces are {models_to_conversion_functions.keys()}")
            conversion_function, canonical_name = models_to_conversion_functions[model.lower]
            self.add_colorimetry(conversion_function(XYZ), canonical_name, **kwargs)

    def add_from_sd(self, tm2714_header, sd, models, **kwargs):
        self.add_from_XYZ(sd_to_XYZ(sd))

    def read(self):
        if self.path:
            if Path(self.path).exists():
                tree = ET.parse(self.path)
                # parse out
                stored = toml.load(path)
                self.colorspace = colorspace if colorspace else stored['attributes']['colorspace']
                self.values = values if values else stored['payload']['values']
            else:
                raise FileNotFoundError(f"could not find tristimulus colorimetry file (.colx) at {path}")
        else:
            self.colorspace = colorspace if colorspace else None
            self.values = values if values else None

    def write(self):
        root = ET.Element('IESTM2714')
        root.attrib = {
            'xmlns': NAMESPACE_EIEIO_COLORIMETRY,
            'version': VERSION_EIEIO_COLORIMETRY
        }
        colorimetry_node = ET.SubElement(root, 'Colorimetry')
        quality_node = ET.SubElement(colorimetry_node, 'ColorimetricQuality')
        quality_node.text = self.colorimetric_quality
        reflection_geo_node = ET.SubElement(colorimetry_node, 'ReflectionGeometry')
        reflection_geo_node.text = self.reflection_geometry
        transmission_geo_node = ET.SubElement(colorimetry_node, 'TransmissionGeometry')
        transmission_geo_node.text = self.transmission_geometry
        bandwith_fwhm_mode = ET.SubElement(colorimetry_node, 'BandwidthFWHM')
        bandwith_fwhm_mode.text = self.bandwidth_fwhm
        bandwith_corr_node = ET.SubElement(colorimetry_node, 'BandwidthCorrected')
        bandwith_corr_node.text = self.bandwidth_corrected_data
        colorspace_node = ET.SubElement(colorimetry_node, 'ColorspaceModel')
        colorspace_node.text = self.colorspace_model_name
        for datum in self.colorspace_data:
            datum_node = ET.SubElement(colorimetry_node, 'ColorspaceData')
            datum_node.text = datum
        tree = ET.ElementTree(root)
        ET.indent(tree, space='    ')
        with open(self.path, 'w') as file:
            file.write(root)
