# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from astropy.wcs import WCS

from azulero import process
from azulero.image import color

Transform = color.Transform
"""
Transformation parameters.

Args:
    iyjh_zero_points: Zero points of each channel
    iyjh_scaling: Scaling of each channel (for white balance)
    iyjh_fwhm: PSF full width at half-maximum of each channel
    sharpen_strength: Unsharp masking strength
    nir_to_l: NIR-to-L rate
    i_to_b: I-to-B rate
    y_to_g: Y-to-G rate
    j_to_r: J-to-R rate
    hue: Hue rotation angle in degrees
    saturation: Saturation gain
    stretch: Stretching parameter
    bw: Black and white points in AB-mag
    bgr_curves: Curve adjustment knots for each channel
"""


def process_iyjh(
    iyjh: np.ndarray,
    wcs: WCS | None = None,
    transform: Transform = Transform(),
    output: str = "",
) -> np.ndarray:
    """
    Process an image according to transformation parameters,
    optionally save intermediate and final images.

    Args:
        iyjh: A stack of the I, Y, J, H arrays (e.g. ``iyjh[1]`` is the NIR-Y channel).
        wcs: The WCS parameters
        transform: The transformation parameters
        output: The output file name (empty string to disable writing)

    Returns:
        A normalized BGR image (i.e. default OpenCV layout).
    """
    # FIXME output not written
    return process.process_iyjh(iyjh, wcs, transform, output)
