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

    def scale(self, *factors):
        self.data *= factors


def parse_slice(text):
    parse_index = lambda i: int(i) if i else None
    return tuple(
        slice(*[parse_index(i) for i in axis.split(":")]) for axis in text.split(",")
    )


def inpaint(tile: Tile, threshold: float):
    mask = np.where(tile.rms > threshold, 1, 0)
    return skinpaint.inpaint_biharmonic(tile.data, mask)
