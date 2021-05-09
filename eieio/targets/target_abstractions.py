# -*- coding: utf-8 -*-
"""
Abstract base classes for targets used in colour science work
===================

Defines an abstract generic meter_desc base class and then a spectroradiometer subclass (but still abstract)

"""

from abc import ABC, abstractmethod

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'TargetBase'
]

class TargetBase(ABC):
    def __init__(self, host, patch_name, log, **kwargs):
        self._host = None
        self.host = host
        if not self.host:
            raise ValueError("No host specified when creating target")
        self._patch_name = None
        self.patch_name = patch_name
        self._log = None
        self.log = log
        if not self.log:
            raise ValueError("No log specified when creating target")

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def patch_name(self):
        return self._patch_name

    @patch_name.setter
    def patch_name(self, value):
        self._patch_name = value

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, value):
        self._log = value

    @abstractmethod
    def set_target_stimulus(self, name, value, log, **kwargs):
        """Set the target's named stimulus (e.g. 'Constant1' for Nuke) to the RGB in value"""
        raise NotImplementedError
