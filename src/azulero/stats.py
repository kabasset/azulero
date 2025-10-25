# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np


def percentiles(data: np.ndarray, *qs: float):
    """
    Compute a list of percentiles without interpolation.
    """
    sorted = data.flatten()
    last = len(sorted) - 1
    sorted.sort()  # TODO partial sort upto `round(max(qs) / 100 * last)`
    return [sorted[round(q / 100 * last)] for q in qs]
