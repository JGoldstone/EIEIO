# -*- coding: utf-8 -*-
"""
measure - command-line tool to take spectral and (optionally) colorimetric measurements
==============================

Collects instructions for a measurement session and executes them.
"""

from socket import gethostname
import os
from pathlib import Path

from eieio.measurement.instructions import Instructions
from eieio.meter.xrite.i1pro import I1Pro
from eieio.measurement.session import MeasurementSession
from eieio.measurement.sample_id_sequence import SampleIDSequence
from colour.io.tm2714 import SpectralDistribution_IESTM2714
from colour.io.tm2714 import Header_IESTM2714
from colour.colorimetry.tristimulus import sd_to_XYZ
from colour.models.cie_xyy import XYZ_to_xy

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    ''
]


def iestm2714_header(**kwargs):
    make = kwargs.get('make', 'Unknown stimulus generator manufacturer')
    model = kwargs.get('model', 'Unknown stimulus generator model')
    description = kwargs.get('description', 'Unknown stimulus being measured')
    document_creator = kwargs.get('creator', os.path.split(os.path.expanduser('~'))[-1])
    report_date = MeasurementSession.timestamp()
    unique_identifier = (gethostname() + ' ' + report_date).replace(' ', '_')
    measurement_equipment = kwargs.get('device', 'Unknown measurement device')
    laboratory = kwargs.get('location', 'Unknown measurement location')
    report_number = Path(os.getcwd()).stem
    return Header_IESTM2714(manufacturer=make, catalog_number=model, description=description,
                            document_creator=document_creator, unique_identifier=unique_identifier,
                            measurement_equipment=measurement_equipment, laboratory=laboratory,
                            report_number=report_number, report_date=report_date)

def iestm2714_header_from_instructions(instructions):
    return iestm2714_header(make=instructions.sample_make, model=instructions.sample_model,
                            description=instructions.sample_description,
                            device=instructions.device_type,
                            location=instructions.location)

def iestm2714_sd(header, spectral_quantity='radiance', reflection_geometry='Unknown reflection geometry'):
    return SpectralDistribution_IESTM2714(header=header, spectral_quantity=spectral_quantity,
                                          reflection_geometry=reflection_geometry, bandwidth_FWHM=25)


class Measurer(object):
    """
    Coordinating object for measuring stimuli with a metering device and writing results to storage.

    Attributes
    ----------
    -   :attr:`~eieio.cli_tools.measure.Measurer.sample_ids`
    -   :attr:`~eieio.cli_tools.measure.Measurer.device`
    """
    def __init__(self, instructions):
        self._instructions = instructions
        self._instructions.merge_eieio_file_defaults()
        self._instructions.merge_command_line_args()
        self._device = None
        self._sample_ids = None
        self._output_dir = self._instructions.output_dir

    @property
    def sample_ids(self):
        return self._sample_ids

    @sample_ids.setter
    def sample_ids(self, ids):
        self._sample_ids = ids

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device):
        self._device = device

    @device.deleter
    def device(self):
        del self._device
        self._device = None

    def _setup_output_dir(self, create_parent_dirs=False, exists_ok=False):
        """
        Creates a directory or verifies the presence of an existing directory into which
        measurement data will be written, optionally creating intermediate directories
        that don't already exist.

        Returns
        -------
        Path
            Path object corresponding to supplied output_dir pathname.

        Raises
        --------
            FileNotFoundError if create_parent_dirs is False and intermediate directories are missing
            FileExistsError if exists_ok is False and the directory already exists

        """
        p = Path(self._output_dir)
        if p.exists():
            if not exists_ok:
                raise RuntimeError(f"measurement base dir `{p}' already exists")
            if not p.is_dir():
                raise FileExistsError(f"measurement base dir `{p}' exists, but is not a directory")
            else:
                if not os.access(p, os.W_OK):
                    raise ProcessLookupError(f"measurement base dir `{p}' exists, but is not writable")
        else:
            output_dir_parent_path = p.parent
            if not output_dir_parent_path.exists():
                if not create_parent_dirs:
                    raise RuntimeError(f"parent dir(s) of measurement base dir `{p}' do not exist")
                p.mkdir(parents=True)
            else:
                p.mkdir()

    def run(self):
        self._setup_output_dir()
        if self._instructions.device_type == 'i1pro':
            self.device = I1Pro()
        lambda_low, lambda_high = self.device.spectral_range_supported()
        lambda_inc = self.device.spectral_resolution()[0]
        wavelengths = range(lambda_low, lambda_high + 1, lambda_inc)
        self.device.set_measurement_mode(self._instructions.mode)
        wait_for_button_press = True
        self.device.calibrate(wait_for_button_press)
        print()
        patch_number = 1
        self.sample_ids = SampleIDSequence(self._instructions.sequence_file)
        self.sample_ids.load()
        session = MeasurementSession(self._output_dir)
        try:
            for sample_id in self.sample_ids.ids:
                prompt = f"sample_name (or RETURN for {sample_id}, or 'exit' to quit the run early):"
                chosen_sample = input(prompt)
                if chosen_sample == 'exit':
                    break
                elif chosen_sample != '':
                    chosen_sample = sample_id
                sd = iestm2714_sd(iestm2714_header_from_instructions(self._instructions))
                self.device.trigger_measurement()
                # color = i1ProAdapter.measuredColorimetry()
                # entry = "%s %.4f %.4f %.4f" % (patch, color[0], color[1], color[2])
                values = self.device.spectral_distribution()
                sd.wavelengths = wavelengths
                sd.values = values
                output_filename = f"sample.{patch_number:04d}.{chosen_sample}.spdx"
                sd.path = str(Path(self._instructions.output_dir, output_filename))
                session.add_spectral_measurement(sd)
                cap_xyz = sd_to_XYZ(sd)
                (x, y) = XYZ_to_xy(cap_xyz)
                if self._instructions.verbose:
                    print(f"patch {chosen_sample}")
                    print(f"\tCIE 1931 XYZ: {cap_xyz[0]:8.4}  {cap_xyz[1]:8.4} {cap_xyz[2]:8.4}")
                    print(f"\tCIE x,y: {x:6.4}, {y:6.4}")
                patch_number += 1
        finally:
            if session.contains_unsaved_measurements():
                session.save()

    def cleanup(self):
        if self.device:
            del self.device


if __name__ == '__main__':
    instance = None
    cleanup_attempted = None
    try:
        main_instructions = Instructions(__name__,
                                         'measure a sequence of stimuli, gathering spectra'
                                         'and (optionally) colorimetry')
        main_instructions.merge_eieio_file_defaults()
        main_instructions.merge_command_line_args()
        instance = Measurer(main_instructions)
        instance.run()
        cleanup_attempted = True
        instance.cleanup()
        instance = None
    finally:
        if instance and not cleanup_attempted:
            instance.cleanup()
