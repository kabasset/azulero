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

    qs = [0.01, 0.05, 0.5, 1, 50, 99, 99.9, 99.95, 99.99, 100]
    stats = percentiles(data[data > 0], qs)
    stats.values = -2.5 * np.log10(stats.values) + zp
    print(stats)

    base_white = stats[99.99]
    dr = (stats[99] - stats[1]) / -2.5  # FIXME no divide?
    sat_frac = np.sum(data > 0.9 * stats[99.9]) / data.size

    print(f"\nBase (p99.99): {base_white:.2f} AB")

    # Adjustment 1: If max is much brighter than p99.99, add headroom
    gap_max_to_p99_99 = stats[99.99] - stats[100]  # Positive if max is brighter
    if gap_max_to_p99_99 > 1.0:
        # Significant gap: very bright outliers exist
        headroom_adj = -min(gap_max_to_p99_99 * 0.3, 1.5)
        print(f"Max is {gap_max_to_p99_99:.2f} mag brighter than p99.99")
        print(f"  → Headroom adjustment: {headroom_adj:.2f} mag")
    else:
        headroom_adj = 0.0
        print(f"Max close to p99.99 (gap: {gap_max_to_p99_99:.2f} mag)")

    # Adjustment 2: Saturation correction
    if sat_frac > 0.001:
        sat_adj = -min(sat_frac * 300, 1.5)
        print(f"Saturation fraction: {sat_frac:.4f} ({sat_frac*100:.2f}%)")
        print(f"  → Saturation adjustment: {sat_adj:.2f} mag")
    else:
        sat_adj = 0.0
        print(f"Saturation: negligible ({sat_frac:.4f})")

    # Adjustment 3: Dynamic range
    if dr > 4.0:
        dr_adj = -(dr - 4.0) * 0.3
        print(f"High DR ({dr:.2f}): {dr_adj:.2f} mag (need headroom)")
    elif dr < 3.5:
        dr_adj = (3.5 - dr) * 0.2
        print(f"Low DR ({dr:.2f}): {dr_adj:+.2f} mag")
    else:
        dr_adj = 0.0
        print(f"Normal DR ({dr:.2f})")

    # Final calculation
    white_point = base_white + headroom_adj + sat_adj + dr_adj
    print(f"\nBefore clipping: {white_point:.2f} AB")

    white_point = min(white_point, zp)

    flux_threshold = 10 ** ((zp - white_point) / 2.5)
    print(f"Final white point: {white_point:.2f} mag AB")
    print(f"  → Flux threshold: {flux_threshold:.1f}")
    print(f"  → Pixels with flux > {flux_threshold:.1f} will approach saturation")
    print(f"=== End White Point Calculation ===\n")

    # Confidence
    confidence = 1.0

    if white_point <= 19.5 or white_point >= 26.5:
        confidence *= 0.7

    if sat_frac > 0.002:
        confidence *= 0.7

    if abs(dr - 3.8) > 0.6:
        confidence *= 0.9

    confidence = np.clip(confidence, 0.3, 1.0)

    return white_point, confidence


if __name__ == "__main__":
    propose_white_point(np.logspace(1, 4, 100_000_000) - 1000, 24.5)
