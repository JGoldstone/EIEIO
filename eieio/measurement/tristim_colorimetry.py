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

    def add_colorimetry(self, header, existing_entries, values, colorspace_name, **kwargs):
        colorimetry_node = ET.SubElement(existing_entries, 'Colorimetry')
        colorspace_node = ET.SubElement(colorimetry_node, 'ColorspaceModel')
        colorspace_node.text = colorspace_name
        for value in values:
            val_node = ET.SubElement(colorimetry_node, 'ColorspaceData')
            val_node.text = value

    def add_from_XYZ(self, XYZ, models, **kwargs):
        models_to_conversion_functions = {
            'cie xyy': (XYZ_to_xyY, 'CIE xyY'),
            'cie xy': (XYZ_to_xy, 'CIE xy')
        }
        for model in models:
            if model.lower not in models_to_conversion_functions:
                raise RuntimeError(f"colorspace `{model}' is not supported: supported colorspaces are {models_to_conversion_functions.keys()}")
            conversion_function, canonical_name = models_to_conversion_functions[model.lower]
            self.add_colorimetry(conversion_function(XYZ), canonical_name, **kwargs)


    def add_from_sd(self, sd, models, **kwargs):
        self.add_from_XYZ(sd_to_XYZ(sd))

    def write(self):
        """
        Write the spectral distribution spectral data to XML file path.

        Returns
        -------
        bool
            Definition success.

        Examples
        --------
        # >>> from os.path import dirname, join
        # >>> from shutil import rmtree
        # >>> from tempfile import mkdtemp
        # >>> directory = join(dirname(__file__), 'tests', 'resources')
        # >>> sd = SpectralDistribution_IESTM2714(
        # ...     join(directory, 'Fluorescent.spdx')).read()
        # >>> temporary_directory = mkdtemp()
        # >>> sd.path = join(temporary_directory, 'Fluorescent.spdx')
        # >>> sd.write()
        # True
        # >>> rmtree(temporary_directory)
        """

        root = ET.Element('IESTM2714')
        root.attrib = {
            'xmlns': NAMESPACE_EIEIO_COLORIMETRY,
            'version': VERSION_EIEIO_COLORIMETRY
        }

        spectral_distribution = None
        for header_element in (self.header, self):
            mapping = header_element.mapping
            element = ET.ElementTree.SubElement(root, mapping.element)
            for specification in mapping.elements:
                element_child = ET.ElementTree.SubElement(element,
                                                       specification.element)
                value = getattr(header_element, specification.attribute)
                element_child.text = specification.write_conversion(value)

            if header_element is self:
                spectral_distribution = element

        # Writing spectral data.
        for (wavelength, value) in tstack([self.wavelengths, self.values]):
            element_child = ET.ElementTree.SubElement(spectral_distribution,
                                                   mapping.data.element)
            element_child.text = mapping.data.write_conversion(value)
            element_child.attrib = {
                mapping.data.attribute:
                    mapping.data.write_conversion(wavelength)
            }

        # xml = minidom.parseString(
        #     ET.ElementTree.tostring(root)).toprettyxml()  # nosec

        # with open(self._path, 'w') as file:
        #     file.write(xml)

        return True
