# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from azulero import sequence


def test_coord_parsing():

    assert sequence.parse_coord("10.5", 100) == 10.5
    assert sequence.parse_coord("-10.5", 100) == 89.5
    assert sequence.parse_coord("10.5%", 200) == 21.0
    assert sequence.parse_coord("-10.5%", 200) == 179.0


def test_zoom_parsing():

    assert sequence.parse_zoom("20%", None, None) == 0.2
    assert sequence.parse_zoom("0.2w", [160, 180], [16, 9]) == 0.02
    assert sequence.parse_zoom("0.8h", [160, 180], [16, 9]) == 0.04


def test_angle_parsing():

    assert sequence.parse_a_deg("20°") == 20
    assert sequence.parse_a_deg("-0.5pi") == -90
