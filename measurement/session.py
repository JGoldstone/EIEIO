# -*- coding: utf-8 -*-
"""
Measurement session structure and I/O
================================

Defines the :class:`measurement.session` class handling directories full of
*IES TM-27-14* spectral data XML files and a supplementary README.md file
documenting the measurement session's motiviation and procedure.

"""

from enum import Enum
from pathlib import Path
from fileseq import findSequencesOnDisk

from colour import SpectralDistribution_IESTM2714

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'MeasurementSession'
]

README_FILENAME = 'README.md'

SPECTRAL_SUFFIX = '.spdx'
COLORIMETRIC_SUFFIX = '.colx'


class MeasurementType(Enum):
    SPECTRAL = 0
    COLORIMETRIC = 1


class MeasurementSession(object):

    @staticmethod
    def format_date(d):
        return d.strftime("%Y-%M-%D%T%h:%M:%S")

    def __init__(self, readme_md, measurement_type: MeasurementType, measurements=None):
        self._readme_md = readme_md
        self._measurement_type = measurement_type
        self._measurements = measurements

    @classmethod
    def load(cls, dir_path):
        if not Path(dir_path).is_dir():
            raise RuntimeError("measurement sessions must be directories")
        readme_path = Path(dir_path) / README_FILENAME
        if not readme_path.exists():
            raise RuntimeError(f"measurement session must have {README_FILENAME} file")
        with open(readme_path, 'r') as readme_file:
            readme_md = readme_file.readline()
        seqs = findSequencesOnDisk(dir_path)
        spectral_seqs = []
        colorimetric_seqs = []
        for seq in seqs:
            if seq.extension == SPECTRAL_SUFFIX:
                spectral_seqs += seq
            elif seq.extension == COLORIMETRIC_SUFFIX:
                colorimetric_seqs += seq
            else:
                pass  # dark metadata, in a sense
        if len(spectral_seqs) and len(colorimetric_seqs):
            raise RuntimeError(f"both spectral and colorimetric data in {dir_path}")
        if not len(spectral_seqs) and not len(colorimetric_seqs):
            raise RuntimeError(f"neither spectral nor colorimetric data in {dir_path}")
        if len(colorimetric_seqs):
            raise RuntimeError("colorimetric measurement sessions are not yet supported")
        measurements = []
        if len(spectral_seqs) > 1:
            raise RuntimeError(f"multiple spectral measurement sets in {dir_path}")
        for idx, _ in enumerate(spectral_seqs[0].frameSet()):
            sd = SpectralDistribution_IESTM2714(Path(dir_path) / spectral_seqs[0]).read()
            measurements += sd
        return MeasurementSession(readme_md, MeasurementType.SPECTRAL, measurements)

    def save(self, dir_path, base_filename):
        if Path(dir_path).exists():
            raise RuntimeError(f"the directory {dir_path} already exists")
        readme_path = Path(dir_path) / README_FILENAME
        with open(readme_path, 'w') as file:
            file.write(self._readme_md)
        for i in range(len(self._measurements)):
            frame_number = 1 + i*10  # 1-based and leave space to insert later
            sd = self._measurements[i]
            sd.path = Path(dir_path) / f"{base_filename}.{frame_number:5}{SPECTRAL_SUFFIX}"
            sd.write()

    def add_measurement(self, measurement):
        self._measurements += measurement
