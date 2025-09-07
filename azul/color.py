# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import cv2

from azul import tile


@dataclass
class Transform(object):
    iyjh_scaling: list
    y_to_b: float
    h_to_l: float
    saturation: float


def iyjh_to_rgb(tile: tile.Tile, transform: Transform):

    tile /= transform.iyjh_scaling

    i, y, j, h = tile.data
    y_to_b = transform.y_to_b
    h_to_l = transform.h_to_l

    rgb = np.zeros((tile.shape[1], tile.shape[2], 3), dtype=np.float32)
    rgb[:, :, 0] = h
    rgb[:, :, 1] = (y + j) * 0.5 if y_to_b == 0 else j
    rgb[:, :, 2] = i if y_to_b == 0 else (i + y * y_to_b) / (1 + y_to_b)
    l = i if h_to_l == 0 else (i + h * h_to_l) / (1 + h_to_l)

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * transform.saturation, 0, 1)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
    lab[:, :, 0] = l * 100

    return cv2.cvtColor(lab, cv2.COLOR_Lab2RGB)
