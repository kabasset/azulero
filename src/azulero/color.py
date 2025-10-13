# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import cv2
from scipy import interpolate
from skimage.filters import unsharp_mask as sksharpen

from azulero import io  # FIXME rm


@dataclass
class Transform(object):
    iyjh_zero_points: np.array
    iyjh_scaling: np.array
    fwhm: np.array
    sharpen: float
    nir_to_l: float
    i_to_b: float
    y_to_g: float
    j_to_r: float
    hue: float
    saturation: float
    stretch: float
    bw: np.array


def sharpen(data, radii, strength):  # FIXME to dedicated module
    if strength == 0:
        return data
    for i in range(len(data)):
        data[i] = sksharpen(data[i], radii[i], strength, True)
    return data


def iyjh_to_rgb(data, transform: Transform):

    data = sharpen(data, transform.fwhm / 2.355, transform.sharpen)
    w = 10 ** ((transform.iyjh_zero_points - transform.bw[1]) / 2.5)
    gains = transform.iyjh_scaling / w
    print(gains)
    data *= gains[:, np.newaxis, np.newaxis]
    io.write_tiff(np.concatenate(data), "normalized.tiff")
    data = normalized_asinh(data, transform)
    io.write_tiff(np.concatenate(data), "stretched.tiff")

    i, y, j, h = data
    l = lerp(transform.nir_to_l, np.median(data[1:], axis=0), data[0])

    rgb = np.zeros((data.shape[1], data.shape[2], 3), dtype=np.float32)
    rgb[:, :, 0] = lerp(transform.j_to_r, j, h)
    rgb[:, :, 1] = lerp(transform.y_to_g, y, j)
    rgb[:, :, 2] = lerp(transform.i_to_b, i, y)
    del i, y, j, h

    hls = cv2.cvtColor(rgb, cv2.COLOR_RGB2HLS)
    hls[:, :, 0] = (hls[:, :, 0] + transform.hue) % 360
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
    black = np.arcsinh(transform.bw[0] * a)
    white = np.arcsinh(a)
    return np.clip((data - black) / (white - black), 0, 1, dtype=np.float32)


def adjust_curve(data: np.array, knots: list):
    x, y = list(map(list, zip(*knots)))
    k = min(len(knots) - 1, 3)
    spline = interpolate.make_interp_spline(x, y, k)
    return np.clip(spline(data), 0.0, 1.0)
