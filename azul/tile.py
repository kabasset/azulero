# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

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
            self.data[i] *= factors[i]
        return self

    def __itruediv__(self, factors):
        for i in range(len(factors)):
            self.data[i] /= factors[i]
        return self


def inpaint(tile: Tile, threshold: float):
    mask = np.where(tile.rms > threshold, 1, 0)
    return skinpaint.inpaint_biharmonic(tile.data, mask)
