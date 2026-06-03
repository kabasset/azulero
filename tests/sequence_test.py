# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import Angle
from astropy import units as u
import numpy as np

from azulero.video import sequence, interp


def test_center_parsing():

    context = sequence.RoamingContext((200, 200), (0, 0), 0, None, "planar")

    assert np.array_equal(
        sequence.parse_center(("10.5px,-10.5px"), context), (10.5, 189.5)
    )
    assert np.array_equal(
        sequence.parse_center(("10.5%,-10.5%"), context), (21.0, 179.0)
    )

    context.mode = "spherical"

    assert np.array_equal(
        sequence.parse_center(("45°,-45°"), context), Angle([45, -45], unit=u.deg)
    )


def test_hfov_parsing():

    context = sequence.RoamingContext((160, 180), (16, 9), 0, None, "planar")

    assert sequence.parse_hfov("20%", context) == 16 / 0.2
    assert sequence.parse_hfov("20%w", context) == 180 * 0.2
    assert sequence.parse_hfov("20 % h", context) == 160 * 0.2 * 16 / 9

    context.mode = "spherical"

    assert sequence.parse_hfov("20°", context) == 20 * u.deg


def test_angle_parsing():

    assert sequence.parse_roll("20°") == 20 * u.deg
    assert sequence.parse_roll("20d") == 20 * u.deg
    assert sequence.parse_roll("60m") == 1 * u.deg
    assert sequence.parse_roll("3600s") == 1 * u.deg
    assert sequence.parse_roll("-0.5pi") == -90 * u.deg


def test_trajectory_sampling():

    start_frame = 10
    stop_frame = 17
    start_centers = [[0, 1], [1, 2], [2, 3]]
    stop_center = [3, 4]
    centers = interp.sin_spline(
        sequence.IndexedValue(start_frame, start_centers),
        sequence.IndexedValue(stop_frame, stop_center),
    )
    assert np.allclose([c[1] for c in centers], [c[0] + 1 for c in centers])
    for c0, c1 in zip(centers[:-1], centers[1:]):
        assert c1[0] > c0[0]
        assert c1[1] > c0[1]
