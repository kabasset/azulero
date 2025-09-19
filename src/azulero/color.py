# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import cv2


@dataclass
class Transform(object):
    iyjh_scaling: np.array
    nir_to_l: float
    y_to_g: float
    i_to_b: float
    saturation: float
    stretch: float
    bw: np.array


def iyjh_to_rgb(data, transform: Transform):

    data *= transform.iyjh_scaling[:, np.newaxis, np.newaxis]

    i, y, j, h = data
    l = lerp(transform.nir_to_l, np.median(data[1:], axis=0), i)

    rgb = np.zeros((data.shape[1], data.shape[2], 3), dtype=np.float32)
    rgb[:, :, 0] = h
    rgb[:, :, 1] = lerp(transform.y_to_g, y, j)
    rgb[:, :, 2] = lerp(transform.i_to_b, i, y)
    del i, y, j, h

    rgb = normalized_asinh(rgb, transform)
    l = normalized_asinh(l, transform)
    del data

    hls = cv2.cvtColor(rgb, cv2.COLOR_RGB2HLS)
    hls[:, :, 2] = np.clip(hls[:, :, 2] * transform.saturation, 0, 1)
    hls[:, :, 1] = l

    return cv2.cvtColor(hls, cv2.COLOR_HLS2RGB)


def lerp(x, a, b):
    if x == 0:
        return b
    if x == 1:
        return a
    return x * a + (1 - x) * b


def channelwise_mul(data, factors):
    for i in range(len(factors)):
        data[i] = data[i] * factors[i]
    return data


def channelwise_div(data, factors):
    for i in range(len(factors)):
        data[i] = data[i] / factors[i]
    return data


def normalized_asinh(data: np.ndarray, transform: Transform):
    a = transform.stretch
    data = np.arcsinh(data * a)
    black, white = np.arcsinh(transform.bw * a)
    return np.clip((data - black) / (white - black), 0, 1, dtype=np.float32)
