# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero import sequence


def test_coord_parsing():

    assert sequence.parse_coord("10.5px", 100) == 10.5
    assert sequence.parse_coord("-10.5px", 100) == 89.5
    assert sequence.parse_coord("10.5%", 200) == 21.0
    assert sequence.parse_coord("-10.5%", 200) == 179.0


def test_zoom_parsing():

    assert sequence.parse_zoom("20%", None, None) == 0.2
    assert sequence.parse_zoom("0.2w", [160, 180], [16, 9]) == 0.5
    assert sequence.parse_zoom("0.2h", [160, 180], [16, 9]) == 0.25


def test_angle_parsing():

    assert sequence.parse_a_deg("20°") == 20
    assert sequence.parse_a_deg("-0.5pi") == -90


def test_trajectory_sampling():

    start_frame = 10
    stop_frame = 17
    start_centers = [[0, 1], [1, 2], [2, 3]]
    stop_centers = [3, 4]
    centers = sequence.sin_spline(
        sequence.KeyValue(start_frame, start_centers),
        sequence.KeyValue(stop_frame, stop_centers),
    )
    assert np.allclose([c[1] for c in centers], [c[0] + 1 for c in centers])
    for c0, c1 in zip(centers[:-1], centers[1:]):
        assert c1[0] > c0[0]
        assert c1[1] > c0[1]
