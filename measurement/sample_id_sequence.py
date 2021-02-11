# -*- coding: utf-8 -*-
"""
Sample ID sequence
================================

Defines a class that holds a sequence of sample IDs
"""

import re

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'SampleIDSequence'
]


class SampleIDSequence(object):
    """
    Manages a sequence of sample names
    """

    def __init__(self, path):
        self.path = path
        self.ids = []

    def num_samples(self):
        return len(self.ids)

    def load(self):
        with open(self.path) as f:
            lines = [x.strip() for x in f]
        for line in lines:
            if line == "":
                continue
            pat = r'^(\w+)\s*$'
            match = re.search(pat, line)
            if match:
                sample_id = match.group(1)
                if sample_id in self.ids:
                    raise RuntimeError("sample IDs must be unique in .sis file")
                self.ids.append(sample_id)
            else:
                raise SyntaxError
