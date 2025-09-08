# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azul import tile


def test_flagging():

    assert tile.VisFlag.valid(0)
    assert tile.VisFlag.invalid(1)
    assert tile.VisFlag.invalid(2)
    assert tile.VisFlag.invalid(3)
    assert tile.VisFlag.invalid(4)
    assert tile.VisFlag.valid(8)

    assert tile.NirFlag.valid(0)
    assert tile.NirFlag.valid(1)
    assert tile.NirFlag.invalid(2)
    assert tile.NirFlag.invalid(3)
    assert tile.NirFlag.invalid(4)
    assert tile.NirFlag.invalid(8)
    assert tile.NirFlag.valid(16)
    assert tile.NirFlag.invalid(2**6)
    assert tile.NirFlag.invalid(2**7)
    assert tile.NirFlag.invalid(2**9)
    assert tile.NirFlag.invalid(2**10)
    assert tile.NirFlag.valid(2**11)
    assert tile.NirFlag.invalid(2**12)


def test_scaling():

    data = np.ones((2, 4, 3), dtype=int) * 12
    raw = data.view(np.ma.MaskedArray)

    raw = tile.channelwise_div(raw, (3, 2))

    assert np.all(raw[0] == 4)
    assert np.all(raw[1] == 6)


def test_inpainting():

    data = np.ones((9, 16, 3))
    mask = np.zeros((9, 16))
    data[1, 1, 1] = 0
    mask[1, 1] = 1

    res = tile.inpaint(data, mask)

    assert np.all(res == 1)
