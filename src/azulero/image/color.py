# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import cv2
from scipy import interpolate
from skimage.filters import unsharp_mask as sksharpen

from azulero.image import tune
from azulero.tools.messaging import logger


@dataclass
class Transform(object):
    iyjh_zero_points: np.ndarray
    iyjh_scaling: np.ndarray
    iyjh_fwhm: np.ndarray
    sharpen_strength: float
    nir_to_l: float
    i_to_b: float
    y_to_g: float
    j_to_r: float
    hue: float
    saturation: float
    stretch: float
    bw: np.ndarray
    curves: list


def sharpen(data, radii, strength):  # TODO to dedicated module
    if strength == 0:
        return data
    for i in range(len(data)):
        data[i] = sksharpen(data[i], radii[i], strength, True)
    return data


def abmag_to_value(mag, zp):
    return 10 ** ((zp - mag) / 2.5)


def stretch_iyjh(iyjh: np.ndarray, transform: Transform):
    w = transform.bw[1]
    if w == 0:
        w = tune.propose_white_point(iyjh[0], transform.iyjh_zero_points[0])
        logger.bullet(f"Auto-tune white point: {w:0.2f}")
    whites = abmag_to_value(w, transform.iyjh_zero_points)
    scaling = (transform.iyjh_scaling / whites)[:, np.newaxis, np.newaxis]
    a = abmag_to_value(w, transform.stretch)
    b = -abmag_to_value(transform.bw[0], w)
    iyjh *= scaling
    return asinh(iyjh, a, b)


def iyjh_to_lbgr(iyjh: np.ndarray, transform: Transform):
    i, y, j, h = iyjh
    lbgr = np.zeros((iyjh.shape[1], iyjh.shape[2], 4), dtype=np.float32)
    lbgr[:, :, 0] = lerp(transform.nir_to_l, np.median(iyjh[1:], axis=0), i)
    lbgr[:, :, 1] = lerp(transform.i_to_b, i, y)
    lbgr[:, :, 2] = lerp(transform.y_to_g, y, j)
    lbgr[:, :, 3] = lerp(transform.j_to_r, j, h)
    return lbgr


def lbgr_to_bgr(lbgr: np.ndarray, transform: Transform):
    hls = cv2.cvtColor(lbgr[:, :, 1:], cv2.COLOR_BGR2HLS)
    hls[:, :, 0] = (hls[:, :, 0] + transform.hue) % 360
    hls[:, :, 2] = np.clip(hls[:, :, 2] * transform.saturation, 0, 1)
    hls[:, :, 1] = lbgr[:, :, 0]
    return cv2.cvtColor(hls, cv2.COLOR_HLS2BGR)


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


def asinh(data: np.ndarray, a: float, black: float):
    b = np.arcsinh(black * a)
    data *= a
    np.arcsinh(data, out=data)
    data -= b
    data /= np.arcsinh(a) - b
    np.clip(data, 0, 1, out=data)
    return data


def adjust_curve(data: np.ndarray, knots: list):
    x, y = list(map(list, zip(*knots)))
    k = min(len(knots) - 1, 3)
    spline = interpolate.make_interp_spline(x, y, k)
    return np.clip(spline(data), 0.0, 1.0, dtype=np.float32)  # TODO inplace
