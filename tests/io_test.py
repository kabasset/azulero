# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero import io


def test_slicing():

    text = ":,3:14"
    slicing = io.parse_slice(text)
    assert slicing == (slice(None, None), slice(3, 14))
    a = np.zeros((9, 16))
    b = a[slicing]
    assert b.shape == (9, 11)
