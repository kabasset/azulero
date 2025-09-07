# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azul import tile


def test_slicing():

    text = ":,3:14"
    slicing = tile.parse_slice(text)
    assert slicing == (slice(None, None), slice(3, 14))
    a = np.zeros((9, 16))
    b = a[slicing]
    assert b.shape == (9, 11)


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
