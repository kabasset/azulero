# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero.tools import stats
from azulero.tools.messaging import logger


def propose_white_point(data: np.ndarray, zp: float):

    logger.debug(f"Compute image percentiles in AB magnitude:")
    qs = [0, 0.01, 0.1, 1, 50, 99, 99.9, 99.95, 100]
    percentiles = stats.percentiles(data[data > 0], qs)
    percentiles.values = list(-2.5 * np.log10(percentiles.values) + zp)
    for q in percentiles:
        logger.debug(f"• {q}: {percentiles[q]}")

    white = percentiles[99.95]

    logger.debug(f"Clipping adjustment:")
    clipping = white - percentiles[100]
    logger.debug(f"• Base white point: {white}")
    logger.debug(f"• Max: {percentiles[100]}")
    logger.debug(f"• Clipping: {clipping}")
    if clipping > 1.0:
        adj = -min(clipping * 0.3, 1.5)
        logger.debug(f"• Adjustment: {adj}")
        white += adj

    logger.debug(f"Saturation adjustment:")
    sat_frac = np.sum(data > 0.9 * percentiles[99.9]) / data.size
    logger.debug(f"• Saturated fraction: {sat_frac}")
    if sat_frac > 0.001:
        adj = -min(sat_frac * 300, 1.5)
        logger.debug(f"• Adjustment: {adj}")
        white += adj

    logger.debug(f"Dynamic range ajustment:")
    dr = percentiles[1] - percentiles[99]
    logger.debug(f"• Dynamic range: {dr}")
    if dr > 10:
        adj = (10 - dr) * 0.12
        logger.debug(f"• High DR adjustment: {adj}")
        white += adj
    elif dr < 8.75:
        adj = (8.75 - dr) * 0.08
        logger.debug(f"• Low DR adjustment: {adj}")
        white += adj

    logger.debug(f"Clip at zero point:")
    logger.debug(f"• Zero point: {zp}")
    logger.debug(f"• White point: {white}")

    return min(white, zp)
