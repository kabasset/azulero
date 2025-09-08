# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import enum

import numpy as np
from skimage.restoration import inpaint as skinpaint


@dataclass
class Channel(object):

    data: np.ndarray
    rms: np.ndarray


class Tile(object):

    def __init__(self, *channels):
        self.data = np.stack([c.data for c in channels])
        self.rms = np.stack([c.rms for c in channels])
        assert self.data.shape == self.rms.shape

    @property
    def shape(self):
        return self.data.shape

    def __imul__(self, factors):
        for i in range(len(factors)):
            self.data[i] = self.data[i] * factors[i]
        return self

    def __itruediv__(self, factors):
        for i in range(len(factors)):
            self.data[i] = self.data[i] / factors[i]
        return self


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


def inpaint(tile: Tile, threshold: float):
    mask = np.where(tile.rms > threshold, 1, 0)
    return skinpaint.inpaint_biharmonic(tile.data, mask)
