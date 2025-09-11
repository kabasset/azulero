# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import cv2

from azul import mask


@dataclass
class Transform(object):
    iyjh_scaling: list  # inverse factors
    y_to_b: float
    h_to_l: float
    saturation: float
    contrast: float
    span: list  # black, white


def iyjh_to_rgb(data, transform: Transform):

    channelwise_div(data, transform.iyjh_scaling)

    i, y, j, h = data
    y_to_b = transform.y_to_b
    h_to_l = transform.h_to_l

    rgb = np.zeros((data.shape[1], data.shape[2], 3), dtype=np.float32)
    rgb[:, :, 0] = h
    rgb[:, :, 1] = (y + j) * 0.5 if y_to_b == 0 else j
    rgb[:, :, 2] = i if y_to_b == 0 else (i + y * y_to_b) / (1 + y_to_b)
    l = i if h_to_l == 0 else (i + h * h_to_l) / (1 + h_to_l)
    del data

    rgb = normalized_asinh(rgb, transform)
    l = normalized_asinh(l, transform)

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * transform.saturation, 0, 1)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    del hsv
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
    del rgb
    lab[:, :, 0] = l * 100
    del l

    return cv2.cvtColor(lab, cv2.COLOR_Lab2RGB)


def channelwise_div(data, factors):
    for i in range(len(factors)):
        data[i] = data[i] / factors[i]
    return data


def normalized_asinh(data: np.ndarray, transform: Transform):
    a = transform.span[1] / transform.contrast
    data = np.arcsinh(data / a)
    black = np.arcsinh(transform.span[0] / a)
    white = np.arcsinh(transform.span[1] / a)
    return np.clip((data - black) / (white - black), 0, 1, dtype=np.float32)
