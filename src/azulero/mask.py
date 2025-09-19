# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import enum
import numpy as np
from skimage.restoration import inpaint as skinpaint


class Flag(enum.Enum):

    @classmethod
    def valid(cls, value):
        for flag in cls:
            if value & 2**flag.value:
                # print(f"{value} & {flag.value} ({flag.name})")
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


def dead_pixels(i, y, j, h):

    return (i == 0, (y == 0) | (j == 0) | (h == 0))


def hot_pixels(i, y, j, h):

    abs_threshold = 10.0
    rel_threshold = 10.0
    hot_i = (i > abs_threshold) & (i > rel_threshold * h)
    hot_y = (y > abs_threshold) & (y > rel_threshold * j)
    hot_j = (j > abs_threshold) & (j > rel_threshold * h)
    hot_h = (h > abs_threshold) & (h > rel_threshold * y)
    return hot_i | hot_y | hot_j | hot_h


def inpaint(data, mask):
    # return cv2.inpaint(data, mask.astype(np.int8), 3, cv2.INPAINT_TELEA) # Won't support 3-channel float
    return skinpaint.inpaint_biharmonic(data, mask, channel_axis=-1)


def _resaturate(x):
    if x <= 0.8:
        return x
    if x >= 0.9:
        return 1
    return 2 * x - 0.8


resaturate = np.vectorize(_resaturate)
