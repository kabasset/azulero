# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.io import fits
import numpy as np

from azulero import stats
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "tune",
        help="Autotune image rendering parameters.",
        description=("Analyse image statistics to propose a white point."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "filename",
        type=str,
        metavar="PATH",
        help="Path to the input data",
    )
    parser.add_argument(
        "--zero",
        type=float,
        default=24.5,
        metavar="ZP",
        help="Zero point",
    )

    parser.set_defaults(func=run)


def run(args):

    timer = Timer()

    print(f"Read input: {args.filename}")
    with fits.open(args.filename) as f:
        data = f[0].data
    print(f"- Shape: {data.shape[0]} x {data.shape[1]}")
    timer.tic_print()

    propose_white_point(data, args.zero)  # FIXME split
    timer.tic_print()


def propose_white_point(data: np.ndarray, zp: float):

    print(f"Compute image statistics:")
    qs = [0, 0.01, 0.1, 1, 50, 99, 99.9, 99.99, 100]
    percentiles = stats.percentiles(data[data > 0], qs)
    percentiles.values = -2.5 * np.log10(percentiles.values) + zp
    for q in percentiles:
        print(f"- {q}: {percentiles[q]}")

    white = percentiles[99.99]

    print(f"Clipping adjustment:")
    clipping = white - percentiles[100]
    print(f"- Base white point: {white}")
    print(f"- Max: {percentiles[100]}")
    print(f"- Clipping: {clipping}")
    if clipping > 1.0:
        adj = -min(clipping * 0.3, 1.5)
        print(f"- Adjustment: {adj}")
        white += adj

    print(f"Saturation adjustment:")
    sat_frac = np.sum(data > 0.9 * percentiles[99.9]) / data.size
    print(f"- Saturated fraction: {sat_frac}")
    if sat_frac > 0.001:
        adj = -min(sat_frac * 300, 1.5)
        print(f"- Adjustment: {adj}")
        white += adj

    print(f"Dynamic range ajustment:")
    dr = percentiles[1] - percentiles[99]
    print(f"- Dynamic range: {dr}")
    if dr > 10:
        adj = (10 - dr) * 0.12
        print(f"- High DR adjustment: {adj}")
        white += adj
    elif dr < 8.75:
        adj = (8.75 - dr) * 0.08
        print(f"- Low DR adjustment: {adj}")
        white += adj

    print(f"Clip at zero point:")
    print(f"- Zero point: {zp}")
    print(f"- White point: {white}")
    return min(white, zp)
