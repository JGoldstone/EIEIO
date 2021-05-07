# -*- coding: utf-8 -*-
"""
Merge old-style outboard colorimetry information in .colx into .spdx JSON_encoded header comment
================================


"""

import sys
from pathlib import Path
from eieio.measurement.measurement import Measurement
from eieio.measurement.colorimetry import Colorimetry

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
]


import xml.etree.ElementTree as ET

from pathlib import Path
import fileseq
import os


def move_frames_to_dir(src_dir, name_pattern, dst_dir):
    seq = fileseq.findSequenceOnDisk(str(Path(src_dir, name_pattern)))
    for ix, _ in enumerate(seq.frameSet()):
        old_path = seq[ix]
        new_path = Path(dst_dir, Path(old_path).name)
        print(f"will call os.rename({old_path}, {new_path})")
        os.rename(old_path, new_path)


def prep_dir_for_merge(src_dir, old_style_sub_dir):
    old_style_dir = Path(src_dir, old_style_sub_dir)
    print(f"will call os.mkdir({old_style_dir})")
    os.mkdir(old_style_dir)
    move_frames_to_dir(src_dir, r'sample.@.spdx', old_style_dir)
    move_frames_to_dir(src_dir, r'sample.@.cie_xyy.colx', old_style_dir)
    move_frames_to_dir(src_dir, r'sample.@.cie_xyz.colx', old_style_dir)


def merge_spdx_colx_samples(src_dir, color_spaces):
    if not color_spaces:
        return
    sub_dir = 'old_style'
    prep_dir_for_merge(src_dir, sub_dir)
    spdx_pattern = str(Path(src_dir, sub_dir, r'sample.@.spdx'))
    seq = fileseq.findSequenceOnDisk(spdx_pattern)
    for ix, _ in enumerate(seq):
        in_spdx = seq[ix]
        out_spdx = str(Path(Path(in_spdx).parents[1], Path(in_spdx).name))
        print(f"{in_spdx} -> {out_spdx}")
        m = Measurement()
        m.path = in_spdx
        m.read()
        m.path = out_spdx
        ns = {'arri': 'http://www.arri.de/camera'}
        for color_space in color_spaces:
            in_colx_name = f"{Path(in_spdx).stem}.{color_space.lower()}.colx"
            in_colx_dir = Path(in_spdx).parent
            in_colx = Path(in_colx_dir, in_colx_name)
            tree = ET.parse(in_colx)
            root = tree.getroot()
            colorimetry = root.find('arri:Colorimetry', ns)
            if not colorimetry:
                raise RuntimeError("couldn't find Colorimetry element in .colx XML")
            color_space = colorimetry.find('arri:ColorSpaceModel', ns).text
            if not color_space:
                raise RuntimeError("couldn't find color space inside Colorimetry element in .colx XML file")
            component_values = []
            for value in colorimetry.findall('arri:ComponentValue', ns):
                v = float(value.text)
                component_values.append(v)
            new_c = Colorimetry('CIE 1931 2 Degree Standard Observer', color_space, 'D65',
                                component_values, origin='measured')
            m.insert_colorimetry(new_c)
        print(f"will write to {m.path}")
        m.write()


if __name__ == '__main__':
    in_base = sys.argv[1]
    merge_spdx_colx_samples(in_base, ["cie_xyy", "cie_xyz"])

