# -*- coding: utf-8 -*-
"""
Peculiarities of the English language
===================

"""

import numpy as np
from functools import partial

from colour.colorimetry import CCS_ILLUMINANTS
from colour.models.rgb import RGB_Colourspace, gamma_function

__author__ = 'Various'
__copyright__ = None
__license__ = None
__maintainer__ = None
__email__ = None
__status__ = 'Production'

__all__ = [
    'oxford_join'
]

# import re

# from Thomas Mansencal:
# print(re.sub(',\s(\'\w+\'")$', ' or \\1', re.sub('\[|\]', '"', str(['foo', 'bar', 'John', 'Doe']))))

# From https://stackoverflow.com/questions/19838976/grammatical-list-join-in-python
def oxford_join(data, conjunction):
    if conjunction not in ['or', 'and', 'nor']:
        raise ValueError("conjunction to oxford_join must be one of 'or', 'and' or 'nor'")
    if len(data) == 1:
        return f"{data[0]}"
    elif len(data) == 2:
        return f"{data[0]} {conjunction} {data[1]}"
    else:
        return ", ".join(tuple(data[:-2]) + tuple([f", {conjunction} ".join(data[-2:])]))

