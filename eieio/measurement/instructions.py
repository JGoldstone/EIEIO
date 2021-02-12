# -*- coding: utf-8 -*-
"""
Instructions - the parameters and sequence of a measurement session
==============================

Collects together a measurement session's device name and parameters, input sequence,
output destination, and any pre- and post-frame hooks.
"""

import os
import sys
import argparse as ap
from eieio.meter.meter_abstractions import Mode

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'Instructions'
]

NAMED_MODES = {'ambient': Mode.ambient, 'emissive': Mode.emissive, 'reflective': Mode.reflective}

class Instructions(object):

    def __init__(self, prog, desc):
        self.args = ap.ArgumentParser(prog=prog, description=desc)
        # TODO make device_choices extensible by looking in a directory at runtime
        # say by looking for modules in the eieio.meter package that conform fully to
        # the eieio.meter.meter_abstractions abstract base class
        device_choices = ['i1pro', 'sekonic']
        # str.lower courtesy of https://stackoverflow.com/questions/27616778/case-insensitive-argparse-choices
        self.args.add_argument('--device', '-d', type=str.lower, choices=device_choices)
        self.args.add_argument('--output_dir', '-o', default=os.getcwd())
        self.args.add_argument('--colorspace', '-c', type=str.lower, choices=['xyz', 'lab'])
        self.args.add_argument('--mode', '-m', type=str.lower, choices=['emissive', 'ambient', 'reflective'])
        self.args.add_argument('--base_measurement_name', '-b')
        self.args.add_argument('--create_parent_dirs', '-p', action='store_true')
        self.args.add_argument('--sequence_file', '-s')
        self.args.add_argument('--frame_preflight')
        self.args.add_argument('--frame_postflight')
        self.args.add_argument('--verbose', '-v', action='store_true')
        self.args.parse_args(namespace=self.args)

    def consistency_check(self):
        # TODO if the device is a sekonic, make sure it's a file:/path URL
        # really you want to pass that to an argument validation class method on Sekonic, no?
        self.args.mode = NAMED_MODES[self.args.mode]
        return True, ''


if __name__ == '__main__':
    desc = 'measure a sequence of stimuli, gathering spectra and (optionally) colorimetry'
    instructions = Instructions('Instructions ( main() )', desc)
    print(instructions)
    consistent, issues = instructions.consistency_check()
    if not consistent:
        print('the following issues were detected in extended argument consistency checking:')
        print(issues)
