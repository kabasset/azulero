# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import cv2
import enum
import numpy as np
from skimage.restoration import inpaint as skinpaint


def channelwise_div(data, factors):
    for i in range(len(factors)):
        data[i] = data[i] / factors[i]
    return data


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
    # COLD = 1
    # SATURATED = 2
    # BAD = 8


class NirFlag(Flag):
    # INVALID = 1
    # DISCONNECTED = 2
    # ZERO_QE = 3
    # SUPER_QE = 6
    # HOT = 7
    # SNOWBALL = 9
    SATURATED = 10
    NL_SATURATED = 12


def bad_pixels(i, y, j, h):

    thresh1 = 10.0  # minimum brightness to be considered as a hot pixel
    thresh2 = 10.0  # checking that it's really a hot pixel (could mask extremely colourful objects)
    maskL = (i > thresh1) & (i > thresh2 * h)
    maskB = (y > thresh1) & (y > thresh2 * j)
    maskG = (j > thresh1) & (j > thresh2 * h)
    maskR = (h > thresh1) & (h > thresh2 * y)
    return maskL | maskB | maskG | maskR | (y == 0) | (j == 0) | (h == 0) | (i == 0)


def repair_bad_pixels(i, y, j, h):

    bad_nir = (y == 0) | (j == 0) | (h == 0)
    bad_vis = i == 0

    indices = np.where(bad_nir & ~bad_vis)
    y[indices] = i[indices]
    j[indices] = i[indices]
    h[indices] = i[indices]

    indices = np.where(~bad_nir & bad_vis)
    i[indices] = (y[indices] + j[indices] + h[indices]) / 3.0

    indices = np.where(bad_nir & bad_vis)
    maskval = np.max(i)
    y[indices] = maskval
    j[indices] = maskval
    h[indices] = maskval


def inpaint(data, mask):
    return skinpaint.inpaint_biharmonic(data, mask, channel_axis=-1)
