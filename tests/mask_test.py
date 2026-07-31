# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero.image import mask


def test_flagging():

    assert mask.VisFlag.valid(0)
    assert mask.VisFlag.invalid(1)
    assert mask.VisFlag.invalid(2)
    assert mask.VisFlag.invalid(3)
    assert mask.VisFlag.invalid(4)
    assert mask.VisFlag.valid(8)

    assert mask.NirFlag.valid(0)
    assert mask.NirFlag.valid(1)
    assert mask.NirFlag.invalid(2)
    assert mask.NirFlag.invalid(3)
    assert mask.NirFlag.invalid(4)
    assert mask.NirFlag.invalid(8)
    assert mask.NirFlag.valid(16)
    assert mask.NirFlag.invalid(2**6)
    assert mask.NirFlag.invalid(2**7)
    assert mask.NirFlag.invalid(2**9)
    assert mask.NirFlag.invalid(2**10)
    assert mask.NirFlag.valid(2**11)
    assert mask.NirFlag.invalid(2**12)


def test_inpainting():

    data = np.ones((9, 16, 3))
    flags = np.zeros((9, 16))
    data[1, 1, 1] = 0
    flags[1, 1] = 1

    res = mask.inpaint(data, flags)

    assert np.all(res == 1)


def test_continent_removal():

    a = np.zeros([1, 10, 10], dtype=np.uint8)
    a[0, 1:3, 1:3] = 1
    a[0, 4:8, 4:8] = 1

    mask.remove_large_components(a, 16)
    assert np.all(a[1:3, 1:3] == 1)
    assert np.all(a[4:8, 4:8] == 0)

    mask.remove_large_components(a, 4)
    assert np.all(a[1:3, 1:3] == 0)


def test_corner_removal():
    m = np.array(
        [
            [
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 0],
            ],
            [
                [0, 1, 1],
                [0, 0, 0],
                [0, 0, 0],
            ],
        ]
    )
    c = mask.clear_corners(m)
    expected = np.array(
        [
            [
                [0, 0, 0],
                [0, 0, 1],
                [0, 0, 0],
            ],
            [
                [0, 1, 0],
                [0, 0, 0],
                [0, 0, 0],
            ],
        ]
    )
    assert np.all(c == expected)


def test_edge_non_removal():
    m = np.array(
        [
            [
                [0, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
            ],
            [
                [0, 1, 1],
                [0, 1, 0],
                [0, 0, 0],
            ],
        ]
    )
    c = mask.clear_corners(m)
    expected = np.array(
        [
            [
                [0, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
            ],
            [
                [0, 1, 1],
                [0, 1, 0],
                [0, 0, 0],
            ],
        ]
    )
    assert np.all(c == expected)
