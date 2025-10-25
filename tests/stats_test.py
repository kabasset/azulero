# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero import stats


def test_percentiles():

    a = np.arange(-42, 10001)
    np.random.shuffle(a)
    qs = [0, 0.01, 0.05, 0.5, 1, 50, 99, 99.9, 99.99, 100]
    p = stats.percentiles(a[a >= 0], qs)
    expected = [0, 1, 5, 50, 100, 5000, 9900, 9990, 9999, 10000]
    assert np.allclose(p.values, expected)
    for i in range(len(qs)):
        assert p[qs[i]] == expected[i]
