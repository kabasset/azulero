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
