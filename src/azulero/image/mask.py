# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import enum
import numpy as np
from skimage.restoration import inpaint as skinpaint
from skimage.segmentation import clear_border as skclear_border
from skimage.measure import label as sklabel
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


def hot_pixels(iyjh):
    i, y, j, h = iyjh
    abs_threshold = 10.0
    rel_threshold = 10.0
    hot_i = (i > abs_threshold) & (i > rel_threshold * h)
    hot_y = (y > abs_threshold) & (y > rel_threshold * j)
    hot_j = (j > abs_threshold) & (j > rel_threshold * h)
    hot_h = (h > abs_threshold) & (h > rel_threshold * y)
    return hot_i | hot_y | hot_j | hot_h


def common_borders_2d(mask):
    res = mask.copy()
    for channel in res:
        skclear_border(channel, out=channel)
    res = np.logical_and.reduce(mask & ~res)  # aggregated mask without borders
    res &= ~skclear_border(res)  # reset remaining inner components
    return res


def corners_2d(mask: np.ndarray):
    labels: np.ndarray = sklabel(mask, background=0, connectivity=1)  # type: ignore
    corners_indices = np.unique(
        [labels[0, 0], labels[0, -1], labels[-1, 0], labels[-1, -1]]
    )
    return np.isin(labels, [i for i in corners_indices if i != 0])


def corners_2d_intersection(mask: np.ndarray):
    return np.logical_and.reduce([corners_2d(channel) for channel in mask])


def corners_2d_union(mask: np.ndarray):
    return np.logical_or.reduce([corners_2d(channel) for channel in mask])


def clear_corners(mask):
    mask &= ~corners_2d_union(mask)
    return mask


def remove_large_components(mask: np.ndarray, threshold: int):
    cvmask = np.astype(np.logical_or.reduce(mask), np.uint8)
    analysis = cv2.connectedComponentsWithStats(cvmask, connectivity=4)
    nb, labels, properties, _ = analysis
    areas = properties[:, cv2.CC_STAT_AREA]
    large = [i for i in range(1, nb) if areas[i] > threshold]
    mask[:, np.isin(labels, large)] = False
    return mask


def inpaint(data: np.ndarray, mask: np.ndarray, axis: int = -1):
    if data.ndim > 2:
        return skinpaint.inpaint_biharmonic(
            data, mask, channel_axis=axis, split_into_regions=True
        )
    return cv2.inpaint(data, mask.astype(np.uint8), 3, cv2.INPAINT_NS)


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
