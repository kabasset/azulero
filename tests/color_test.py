# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azul import color


def test_scaling():

    data = np.ones((2, 4, 3), dtype=int) * 12
    raw = data.view(np.ma.MaskedArray)

    raw = color.channelwise_div(raw, (3, 2))

    assert np.all(raw[0] == 4)
    assert np.all(raw[1] == 6)
