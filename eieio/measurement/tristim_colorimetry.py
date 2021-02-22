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

    def write(self):
        """
        Write the spectral distribution spectral data to XML file path.

        Returns
        -------
        bool
            Definition success.

        Examples
        --------
        >>> from os.path import dirname, join
        >>> from shutil import rmtree
        >>> from tempfile import mkdtemp
        >>> directory = join(dirname(__file__), 'tests', 'resources')
        >>> sd = SpectralDistribution_IESTM2714(
        ...     join(directory, 'Fluorescent.spdx')).read()
        >>> temporary_directory = mkdtemp()
        >>> sd.path = join(temporary_directory, 'Fluorescent.spdx')
        >>> sd.write()
        True
        >>> rmtree(temporary_directory)
        """

        root = ElementTree.Element('IESTM2714')
        root.attrib = {
            'xmlns': NAMESPACE_IESTM2714,
            'version': VERSION_IESTM2714
        }

        spectral_distribution = None
        for header_element in (self.header, self):
            mapping = header_element.mapping
            element = ElementTree.SubElement(root, mapping.element)
            for specification in mapping.elements:
                element_child = ElementTree.SubElement(element,
                                                       specification.element)
                value = getattr(header_element, specification.attribute)
                element_child.text = specification.write_conversion(value)

            if header_element is self:
                spectral_distribution = element

        # Writing spectral data.
        for (wavelength, value) in tstack([self.wavelengths, self.values]):
            element_child = ElementTree.SubElement(spectral_distribution,
                                                   mapping.data.element)
            element_child.text = mapping.data.write_conversion(value)
            element_child.attrib = {
                mapping.data.attribute:
                    mapping.data.write_conversion(wavelength)
            }

        xml = minidom.parseString(
            ElementTree.tostring(root)).toprettyxml()  # nosec

        with open(self._path, 'w') as file:
            file.write(xml)

        return True
