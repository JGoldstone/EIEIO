# -*- coding: utf-8 -*-
"""
meter_errors - a subclass of exceptions specific to metering
==============================

Collects instructions for a measurement session and executes them.
"""
__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'NotYetImplemented', 'UnsupportedCapability', 'UnsupportedMeasurementMode', 'UnsupportedObserver'
]


class MeterException(Exception):
    """A base class for EIEIO metering exceptions"""


# https://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python
class NotYetImplemented(MeterException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.details = kwargs.get('details')


class UnsupportedCapability(MeterException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.details = kwargs.get('details')


class UnsupportedMeasurementMode(MeterException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.details = kwargs.get('details')


class UnsupportedObserver(MeterException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.details = kwargs.get('details')
