# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import enum
import numpy as np
from skimage.restoration import inpaint as skinpaint
from skimage.segmentation import clear_border as skclear_border
import cv2


class Flag(enum.Enum):

    @classmethod
    def valid(cls, value):
        for flag in cls:
            if value & 2**flag.value:
                return False
        return True

    @classmethod
    def invalid(cls, value):
        return not cls.valid(value)


class VisFlag(Flag):
    HOT = 0
    COLD = 1
    SATURATED = 2
    BAD = 8


class NirFlag(Flag):
    INVALID = 1
    DISCONNECTED = 2
    ZERO_QE = 3
    SUPER_QE = 6
    HOT = 7
    SNOWBALL = 9
    SATURATED = 10
    NL_SATURATED = 12


def dead_pixels(iyjh):
    return iyjh == 0


def clear_borders(mask):
    for channel in mask:
        skclear_border(channel, out=channel)
    return mask


def hot_pixels(i, y, j, h):

    abs_threshold = 10.0
    rel_threshold = 10.0
    hot_i = (i > abs_threshold) & (i > rel_threshold * h)
    hot_y = (y > abs_threshold) & (y > rel_threshold * j)
    hot_j = (j > abs_threshold) & (j > rel_threshold * h)
    hot_h = (h > abs_threshold) & (h > rel_threshold * y)
    return hot_i | hot_y | hot_j | hot_h


def remove_large_components(mask: np.ndarray, threshold: int):
    cvmask = np.astype(np.logical_or.reduce(mask), np.uint8)
    res = []
    if not threshold:
        return res
    analysis = cv2.connectedComponentsWithStats(cvmask, connectivity=4)
    nb, labels, properties, _ = analysis
    for i in range(1, nb):
        area = properties[i, cv2.CC_STAT_AREA]
        if area >= threshold:
            mask[:, labels == i] = False
            res.append(area)
    return res


def inpaint(data: np.ndarray, mask: np.ndarray, axis: int = -1):
    if data.ndim > 2:
        return skinpaint.inpaint_biharmonic(
            data, mask, channel_axis=axis, split_into_regions=True
        )
    return cv2.inpaint(data, mask.astype(np.uint8), 3, cv2.INPAINT_NS)
    # return skinpaint.inpaint_biharmonic(data, mask)


def _resaturate(x):
    """
    Apply ``f(x) = x + x**2 - x**3``.

    This is the simplest polynomial with:

    * ``f(0) = 0``
    * ``f(1) = 1``
    * ``f'(0) = 1``
    * ``f'(1) = 0``

    It is very similar to sinc, but much faster to compute.
    """
    return x + x * x - x * x * x


def resaturate(data):
    if len(data) == 0:
        return data
    return np.vectorize(_resaturate)(data)
