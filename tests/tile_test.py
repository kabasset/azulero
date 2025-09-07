# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azul import tile


def test_scaling():

    data = np.ones((2, 3), dtype=int)
    rms = np.ones((2, 3))
    channel = tile.Channel(data, rms)
    raw = tile.Tile(channel, channel)

    raw *= (2, 3)

    assert np.all(raw.data[0] == 2)
    assert np.all(raw.data[1] == 3)


def test_inpainting():

    data = np.ones((4, 9, 16))
    rms = np.zeros((4, 9, 16))
    threshold = 10
    data[1, 1, 1] = 0
    rms[1, 1, 1] = threshold + 1

    channel = tile.Channel(data, rms)

    raw = tile.Tile(channel, channel, channel, channel)
    res = tile.inpaint(raw, threshold)

    assert np.all(res == 1)
