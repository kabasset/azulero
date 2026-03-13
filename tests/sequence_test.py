# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np

from azulero import sequence


def test_center_parsing():

    assert sequence.parse_center(["10.5px", "-10.5px"], [100, 100]) == (10.5, 89.5)
    assert sequence.parse_center(["10.5%", "-10.5%"], [200, 200]) == (21.0, 179.0)
    assert sequence.parse_center(["45°", "-45°"], None) == SkyCoord(
        ra=45 * u.deg, dec=-45 * u.deg, frame="icrs"
    )


def test_zoom_parsing():

    assert sequence.parse_zoom("20%", None, None) == 0.2
    assert sequence.parse_zoom("0.2w", [160, 180], [16, 9]) == 16 / (0.2 * 180)
    assert sequence.parse_zoom("0.2h", [160, 180], [16, 9]) == 9 / (0.2 * 160)
    assert sequence.parse_zoom("20°", None, None) == 20 * u.deg


def test_angle_parsing():

    assert sequence.parse_angle("20°") == 20 * u.deg
    assert sequence.parse_angle("-0.5pi") == -90 * u.deg


def test_trajectory_sampling():

    start_frame = 10
    stop_frame = 17
    start_centers = [[0, 1], [1, 2], [2, 3]]
    stop_center = [3, 4]
    centers = sequence.sin_spline({start_frame: start_centers, stop_frame: stop_center})
    assert np.allclose([c[1] for c in centers], [c[0] + 1 for c in centers])
    for c0, c1 in zip(centers[:-1], centers[1:]):
        assert c1[0] > c0[0]
        assert c1[1] > c0[1]
