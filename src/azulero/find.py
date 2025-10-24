# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astroquery.simbad import Simbad
import sys


def object_radec(name: str):
    res = Simbad().query_object(name)
    assert len(res) > 0, f"Object not found: {name}"
    assert len(res) < 2, f"Several objects found: {name}"
    return float(res[0]["ra"]), float(res[0]["dec"])


def radec_tile(radec: tuple):
    return int(radec[0])  # FIXME


def object_tile(name: str):
    return radec_tile(object_radec(name))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"{arg} @ {object_radec(arg)} -> {object_tile(arg)}")
