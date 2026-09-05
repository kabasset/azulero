# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np
import scipy.interpolate as interp

from azulero.video import sequence


def sin_sequence(key_frames: list[sequence.IndexedValue]):
    """
    Interpolate parameters over a sequence of frames with sine sampling.
    """
    res = []
    for start, stop in zip(key_frames[:-1], key_frames[1:]):
        if isinstance(start.value, list):
            res += [*sin_spline(start, stop)]
        else:
            res += sin_step(start, stop)
    # TODO prepend first value if first frame > 0
    return res


def sin_step(start: sequence.IndexedValue, stop: sequence.IndexedValue):
    """
    Linearly interpolate parameters between two frames with sine sampling.
    """
    stop_value = stop.value[0] if isinstance(stop.value, list) else stop.value
    return [
        lerp(1 - u, start.value, stop_value)
        for u in sin_sampling(start.index, stop.index)
    ]


def lerp(x, a, b):
    if x == 0:
        return b
    if x == 1:
        return a
    return x * a + (1 - x) * b


def sin_spline(start: sequence.IndexedValue, stop: sequence.IndexedValue):
    """
    Spline-interpolate trajectory between knots with sine sampling.
    """
    knots = np.stack([*start.value, stop.value])
    b = interp.make_interp_spline(
        np.linspace(0, 1, len(knots)), knots, k=min(3, len(knots) - 1)
    )
    u = sin_sampling(start.index, stop.index)
    return b(u)


def sin_sampling(start, stop):
    """
    Sine sampling between two bounds.

    Args:
        start: Start frame index.
        stop: Stop frame index.

    Returns:
        An array of sine-spaced values between 0 and 1.
    """
    return np.sin(np.linspace(0, 1, stop - start) * np.pi - np.pi / 2) / 2 + 0.5
