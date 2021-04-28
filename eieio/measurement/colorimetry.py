# -*- coding: utf-8 -*-
"""
Stand-in tristimulus colorimetry class
================================

Defines the :class:`spectral_measurement.session.TristimulusColorimetryMeasurement` class handling
XML files with colorimetric data (with suffix .colx).

The stored data can originate two ways:
direct spectral_measurement, that is, they are the immediate output of a measuring instrument
derivation, which is to say, they are conversions from direectly measured data

The stored data are associated with a colorspace model. No associated image state is
maintained, and the data are carried as floating-point numbers without any prejudice
as to what conversion functions, if any, might have been applied to the output of
the measuring instrument or to the conversions therefrom.

The stored data are immutable.
"""

from enum import Enum
import re
from pathlib import Path
from functools import partial

from colour.constants import DEFAULT_FLOAT_DTYPE
from colour.models.common import COLOURSPACE_MODELS, COLOURSPACE_MODELS_AXIS_LABELS
from colour.colorimetry.tristimulus_values import sd_to_XYZ

from colour.models.cie_xyy import XYZ_to_xy, XYZ_to_xyY
from colour.models.cie_lab import XYZ_to_Lab
from colour.models.cie_luv import XYZ_to_Luv
from colour.io.tm2714 import Element_Specification_IESTM2714, Header_IESTM2714
from colour.utilities import Structure, is_string, is_numeric
import xml.etree.ElementTree as ET
from xml.dom import minidom
import toml


__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Colorimetry', 'Origin', 'Colorimetry_IESTM2714'
]

VERSION_EIEIO_COLORIMETRY = '0.1'
NAMESPACE_EIEIO_COLORIMETRY = 'http://www.arri.de/camera'


def canonical_observer(observer):
    names_and_aliases = {
        'CIE 1931 2 Degree Standard Observer': ['cie 1931 2 degree standard observer',
                                                'cie 1931',
                                                '2 degree',
                                                '2º',
                                                'two degree 1931'],
        'CIE 1964 10 Degree Standard Observer': ['cie 1964 10 degree standard observer',
                                                 'cie 1964',
                                                 '10 degree',
                                                 '10º',
                                                 '10 degree 1964']
    }
    for name, aliases in names_and_aliases.items():
        if observer.lower().replace('_', ' ') in aliases:
            return name
    raise RuntimeError(f"observer `{observer}' is not a known standard observer")


class Colorimetry(object):
    def canonical_colorspace_model(self, model):
        lc_models = list((model.lower() for model in COLOURSPACE_MODELS))
        clean_model = model.lower.replace('_',' ')
        if mclean_model not in lc_models:
            raise RuntimeError(f"colorspace model `{model}' not in colour.common.COLOURSPACE_MODELS")
        return COLOURSPACE_MODELS[lc_models.index(clean_model)]

    def __init__(self, observer, colorspace_model, component_values, reference_white=None):
        self._mapping = Structure(
            **{
                'element':
                    'Colorimetry',
                'elements':
                    (Element_Specification_IESTM2714('Observer', 'observer'),
                     Element_Specification_IESTM2714('ColorSpaceModel', 'colorspace_model'),
                     Element_Specification_IESTM2714('ComponentValues', 'component_values'),
                     Element_Specification_IESTM2714('ReferenceWhite', 'reference_white'))
            })
        self._observer = canonical_observer(observer)
        self._colorspace_model = self.canonical_colorspace_model(colorspace_model)
        self._component_labels = COLOURSPACE_MODELS_AXIS_LABELS[self._colorspace_model]
        self._component_values = component_values
        self._reference_white = reference_white

    def mapping(self):
        """
        Getter property for the mapping structure.

        Returns
        -------
        Structure
            Mapping structure.
        """
        return self._mapping

    @property
    def observer(self):
        """
        Getter property for the name of the colorimetric observer used in computing XYZ values

        Returns
        -------
        unicode
            observer
        """
        return self._observer

    @property
    def colorspace_model(self):
        """
        Getter property for the name of the color model used to represent the color

        Returns
        -------
        unicode
            Model name
        """
        return self._colorspace_model

    @property
    def component_labels(self):
        """
        Getter property for the labels of the components of the color model used to represent the color

        Returns
        -------
        sequence of unicode
            sequence of unicode values representing the names of the components of the color model used to represent the color
        """
        return self._component_labels

    def component_names(self):
        def asciify(label):
            result = label
            # replace $x^\\prime$ with x'
            prime_pattern = re.compile(r'\$(.+)\^\\prime\$')
            prime_match = prime_pattern.match(result)
            if prime_match:
                result = f"{prime_match.group(1)}'"
            # replace $x^*$ with x*
            star_pattern = re.compile(r'\$(.+)\^\*\*')
            star_match = star_pattern.match(result)
            if star_match:
                result = f"{star_match}*"
            # replace $X_Y$ with Xy
            subscript_pattern = re.compile(r'\$([A-Z])_([A-Z])\$')
            subscript_match = subscript_pattern.match(result)
            if subscript_match:
                result = f"{subscript_match.group(1)}{subscript_match.group(2).lower()}"
            return result
        return (asciify(label) for label in self.component_labels)

    @property
    def component_values(self):
        """
        Getter property for the values of the components of the color model used to represent the color

        Returns
        -------
        sequence of float
            sequence of float values representing the components of the color model used to represent the color
        """
        return self._component_values

    @property
    def reference_white(self):
        """
        Getter property for the values of the components of the reference white.

        Returns
        -------
        sequence of float
            sequence of float values representing the components of reference whilte
        """
        return self._reference_white

    def write(self, parent):
        for elem_spec in self.mapping().elements:
            if elem_spec.element == 'ComponentValues':
                for i, value in enumerate(self.component_values):
                    label = self.component_labels[i]
                    value_elem = ET.SubElement(parent, 'ComponentValue')
                    value_elem.text = elem_spec.write_conversion(value)
                    value_elem.attrib = {'Label': label}
            else:
                elem = ET.SubElement(parent, elem_spec.element)
                value = getattr(self, elem_spec.attribute)
                elem.text = elem_spec.write_conversion(value)

class Origin(Enum):
    UNKNOWN = 0
    MEASURED = 1
    DERIVED = 2
    SYNTHESIZED = 3


class Colorimetry_IESTM2714(object):
    """
    Colorimetric measurements in the spirit of IES TM 2714's representation of spectral measurements.

    CxF is probably the better canonical representation but its specification is huge.
    """
    def __init__(self,
                 path=None,
                 header=None,
                 colorimetric_quantity=None,
                 origin=None,
                 reflection_geometry=None,
                 transmission_geometry=None,
                 bandwidth_FWHM=None,
                 bandwidth_corrected=None,
                 colorimetry=None):
        self._mapping = Structure(
            **{
                'element': 'Colorimetry',
                'elements':
                    (Element_Specification_IESTM2714('ColorimetricQuantity',
                                                     'colorimetric_quantity'),
                     Element_Specification_IESTM2714('Origin',
                                                     'origin',
                                                     write_conversion=(
                                                         lambda x: x.name.lower())),
                     Element_Specification_IESTM2714('ReflectionGeometry',
                                                     'reflection_geometry'),
                     Element_Specification_IESTM2714('TransmissionGeometry',
                                                     'transmission_geometry'),
                     Element_Specification_IESTM2714(
                         'BandwidthFWHM',
                         'bandwidth_FWHM',
                         read_conversion=DEFAULT_FLOAT_DTYPE),
                     Element_Specification_IESTM2714(
                         'BandwidthCorrected',
                         'bandwidth_corrected',
                         read_conversion=(
                             lambda x: True if x == 'true' else False),
                         write_conversion=(
                             lambda x: 'true' if x is True else 'False'))),
                'data':
                    Element_Specification_IESTM2714(
                        'Colorimetry', 'colorimetry', required=True)
            })
        self._path = None
        self.path = path
        self._header = None
        self.header = header if header is not None else Header_IESTM2714()
        self._colorimetric_quantity = None
        self.colorimetric_quantity = colorimetric_quantity
        self._origin = None
        self.origin = origin
        self._reflection_geometry = None
        self.reflection_geometry = reflection_geometry
        self._transmission_geometry = None
        self.transmission_geometry = transmission_geometry
        self._bandwidth_FWHM = None
        self.bandwidth_FWHM = bandwidth_FWHM
        self._bandwidth_corrected = None
        self.bandwidth_corrected = bandwidth_corrected
        self._colorimetry = None
        self.colorimetry = colorimetry

    def mapping(self):
        """
        Getter property for the **self.mapping** structure.

        Returns
        -------
        Structure
            Mapping structure.
        """

        return self._mapping

    @property
    def path(self):
        """
        Getter property for the **self.path** property.

        Returns
        -------
        unicode
            Path.
        """

        return self._path

    @path.setter
    def path(self, value):
        """
        Setter for the **self.path** property.

        Parameters
        ----------
        value: unicode
            path from which or to which the spectral_measurement will be read or written
        """
        if value is not None:
            assert is_string(value), f"path attribute: `{value}' is not a `string'-like object"
        self._path = value

    @property
    def header(self):
        """
        Getter and setter property for the header.

        Returns
        -------
        Header_IESTM2714
            Header.
        """

        return self._header

    @header.setter
    def header(self, value):
        """
        Setter for the **self.header** property.

        Parameters
        ----------
        value : Header_IESTM2714
            Value to which the **self.header** property should be set.
        """
        if value is not None:
            assert isinstance(value, Header_IESTM2714), (
                '"{0}" attribute: "{1}" is not a "Header_IESTM2714" '
                'instance!'.format('header', value))
        self._header = value

    @property
    def colorimetric_quantity(self):
        """
        Getter for the **self.colorimetric_quantity** property (radiance, luminance, &c).

        Returns
        -------
        unicode
            Model name
        """
        return self._colorimetric_quantity

    @colorimetric_quantity.setter
    def colorimetric_quantity(self, value):
        """
        Setter for the **self.colorimetric_quantity** property (radiance, luminance, &c).

        Parameters
        ----------
        value: unicode
            value to which the model_name property should be set.
        """
        if value is not None:
            assert is_string(value), f"proposed colorimetric value `{value}' is not a `string'-like object"
        self._colorimetric_quantity = value

    @property
    def origin(self):
        """
        Getter for the **self.origin** property (measured vs. derived vs. synthesized).

        Returns
        -------
        unicode
            origin
        """
        return self._origin

    @origin.setter
    def origin(self, value):
        """
        Setter for the **self.origin** property (measured vs. derived vs. synthesized).

        Parameters
        ----------
        value: unicode
            value to which the origin property should be set.
        """
        if value is not None:
            assert isinstance(value, Origin), f"proposed origin attribute value `{value}' is not an Origin enum value"
        self._origin = value

    @property
    def reflection_geometry(self):
        """
        Getter for the **self.reflection_geometry** property.

        Returns
        -------
        unicode
            Reflection geometry.
        """

        return self._reflection_geometry

    @reflection_geometry.setter
    def reflection_geometry(self, value):
        """
        Setter for the **self.reflection_geometry** property.

        Parameters
        ----------
        value : unicode
            value to which the **self.reflection_geometry** should be s4t.
        """
        if value is not None:
            assert is_string(value),\
                f"proposed reflection geometry attribute value `{value}' is not a string-like object"
        self._reflection_geometry = value

    @property
    def transmission_geometry(self):
        """
        Getter for the **self.transmission geometry** property.

        Returns
        -------
        unicode
            Transmission geometry.
        """
        return self._transmission_geometry

    @transmission_geometry.setter
    def transmission_geometry(self, value):
        """
        Setter for the **self.transmission_geometry** property.

        Parameters
        ----------
        value : unicode
            value to which the **self.transmission_geometry** propertyshould be s4t.
        """
        if value is not None:
            assert is_string(value), (
                '"{0}" attribute: "{1}" is not a "string" like object!'.format(
                    'transmission_geometry', value))

        self._transmission_geometry = value

    @property
    def bandwidth_FWHM(self):
        """
        Getter and setter property for the full-width half-maximum bandwidth.

        Returns
        -------
        numeric
            Full-width half-maximum bandwidth.
        """

        return self._bandwidth_FWHM

    @bandwidth_FWHM.setter
    def bandwidth_FWHM(self, value):
        """
        Setter for the **self.bandwidth_FWHM** property.

        Parameters
        ----------
        value : numeric
            Value to set the full-width half-maximum bandwidth with.
        """

        if value is not None:
            assert is_numeric(value), (
                '"{0}" attribute: "{1}" is not a "numeric"!'.format(
                    'bandwidth_FWHM', value))

        self._bandwidth_FWHM = value

    @property
    def bandwidth_corrected(self):
        """
        Getter and setter property for whether bandwidth correction has been
        applied to the measured data.

        Returns
        -------
        bool
            Whether bandwidth correction has been applied to the measured data.
        """

        return self._bandwidth_corrected

    @bandwidth_corrected.setter
    def bandwidth_corrected(self, value):
        """
        Setter for the **self.bandwidth_corrected** property.

        Parameters
        ----------
        value : bool
            Whether bandwidth correction has been applied to the measured data.
        """
        if value is not None:
            assert isinstance(value, bool), (
                '"{0}" attribute: "{1}" is not a "bool" instance!'.format(
                    'bandwidth_corrected', value))
        self._bandwidth_corrected = value

    def add_from_XYZ(self, header, observer, model, XYZ, illum_XYZ=None):
        obs = canonical_observer(observer)
        self.colorimetry = Colorimetry(obs, model, XYZ)
        self.header = header
        # models_to_conversion_functions = {
        #     'cie xyy': (XYZ_to_xyY, 'CIE xyY'),
        #     'cie xy': (XYZ_to_xy, 'CIE xy'),
        #     'cie lab': (partial(XYZ_to_Lab, illum_XYZ), 'CIE Lab'),
        #     'cie luv': (XYZ_to_Luv, 'CIE Luv')
        # }
        # for model in models:
        #     if model.lower not in models_to_conversion_functions:
        #         raise RuntimeError(f"colorspace `{model}' is not supported: supported colorspaces are {models_to_conversion_functions.keys()}")
        #     conversion_function, canonical_name = models_to_conversion_functions[model.lower]
        #     self.add_colorimetry(conversion_function(XYZ), canonical_name, **kwargs)

    def add_from_sd(self, header, observer, model, sd, illum_XYZ=None):
        XYZ = sd_to_XYZ(sd)
        self.add_from_XYZ(header, observer, model, XYZ, illum_XYZ)

    # def read(self):
    #     if self.path:
    #         if Path(self.path).exists():
    #             tree = ET.parse(self.path)
    #             # parse out
    #             stored = toml.load(path)
    #             self.colorspace = colorspace if colorspace else stored['attributes']['colorspace']
    #             self.values = values if values else stored['payload']['values']
    #         else:
    #             raise FileNotFoundError(f"could not find tristimulus colorimetry file (.colx) at {self.path}")
    #     else:
    #         self.colorspace = colorspace if colorspace else None
    #         self.values = values if values else None

    def write_header(self, parent):
        header_group = ET.SubElement(parent, self.header.mapping.element)
        for header_elem in self.header.mapping.elements:
            child = ET.SubElement(header_group, header_elem.element)
            value = getattr(self.header, header_elem.attribute)
            child.text = header_elem.write_conversion(value)

    def write(self):
        root = ET.Element('IESTM2714')
        root.attrib = {
            'xmlns': NAMESPACE_EIEIO_COLORIMETRY,
            'version': VERSION_EIEIO_COLORIMETRY
        }
        self.write_header(root)
        for element_spec in self.mapping().elements:
            name = element_spec.element
            value = getattr(self, element_spec.attribute)
            child = ET.SubElement(root, name)
            child.text = element_spec.write_conversion(value)
        colorimetric_node_name = self.mapping().data.element
        colorimetric_node = ET.SubElement(root, colorimetric_node_name)
        self.colorimetry.write(colorimetric_node)
        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(self.path)
