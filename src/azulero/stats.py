# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np


@dataclass
class KeysValues:
    """
    Ordered, possibly-float indexed, dict.
    """

    keys: list
    values: list

    def __iter__(self):
        return iter(self.keys)

    def __getitem__(self, q):
        i = self.keys.index(q)
        return self.values[i]

    def __repr__(self) -> str:
        return (
            "{" + ", ".join(f"{k}: {v}" for k, v in zip(self.keys, self.values)) + "}"
        )


def percentiles(data: np.ndarray, qs: list):
    """
    Compute a list of percentiles without interpolation.
    """
    sorted = data.flatten()
    last = len(sorted) - 1
    sorted.sort()  # TODO partial sort upto `round(max(qs) / 100 * last)`
    return KeysValues(qs, [sorted[round(q / 100 * last)] for q in qs])


def propose_white_point(data: np.ndarray, zp: float):

    print(f"Compute image statistics:")
    qs = [0, 0.01, 0.1, 1, 50, 99, 99.9, 99.99, 100]
    stats = percentiles(data[data > 0], qs)
    stats.values = -2.5 * np.log10(stats.values) + zp
    for q in stats:
        print(f"- {q}: {stats[q]}")

    white = stats[99.99]

    print(f"Clipping adjustment:")
    clipping = white - stats[100]
    print(f"- Base white point: {white}")
    print(f"- Max: {stats[100]}")
    print(f"- Clipping: {clipping}")
    if clipping > 1.0:
        adj = max(clipping * 0.3, -1.5)
        print(f"- Adjustment: {adj}")
        white += adj

    print(f"Saturation adjustment:")
    sat_frac = np.sum(data > 0.9 * stats[99.9]) / data.size
    print(f"- Saturated fraction: {sat_frac}")
    if sat_frac > 0.001:
        adj = -min(sat_frac * 300, 1.5)
        print(f"- Adjustment: {adj}")
        white += adj

    print(f"Dynamic range ajustment:")
    dr = stats[1] - stats[99]
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


if __name__ == "__main__":
    w = propose_white_point(np.logspace(1, 4, 100_000_000) - 1000, 24.5)
    print(w)
