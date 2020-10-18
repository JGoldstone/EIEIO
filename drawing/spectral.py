# -*- coding: utf-8 -*-
"""
spectral
========

Classes and objects for graphing spectral distributions
"""
import colour_datasets
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2020 Lilliputian Pictures LLC'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'joseph.goldstone@mac.com'
__status__ = 'Experimental'

__all__ = [

]

LEDS = colour_datasets.load("4051012")
PEAK_SD = LEDS['556nm - LED 11 - Brendel (2020)']

print(f"There are {len(LEDS)} LED spectra")


def plot_distributions_by_wavelength(sds, **kwargs):
    """
    The most basic of spectral drawing functions.

    Parameters
    ----------
    sds : array-like
        sequence of SpectralDistribution objects
    kwargs

    Returns
    -------

    """
    if not sds:
        return
    shape = None
    wavelengths = None
    for sd in sds.values():
        if not shape:
            shape = sd.shape
        elif sd.shape != shape:
            raise RuntimeError("NYI: different shapes")
        if not wavelengths:
            wavelengths = [wavelength for wavelength in sd.wavelengths]
    n_sds = len(sds)
    n_wavelengths = len(wavelengths)
    values = np.zeros((n_wavelengths, n_sds))
    for i, sd in enumerate(sds.values()):
        values[:,i] = sd.values
    indices = [f"{round(wavelength)}nm" for wavelength in wavelengths]
    columns = [key for key in sds.keys()]
    df = pd.DataFrame(values, columns=columns, index=indices)
    colors = px.colors.qualitative.Plotly
    fig = go.Figure()
    for i, column in enumerate(columns):
        fig.add_traces(go.Scatter(x=df.index, y=df[column], mode='lines', line=dict(color=colors[i % len(colors)])))
    fig.show()


if __name__ == '__main__':
    plot_distributions_by_wavelength(LEDS)


