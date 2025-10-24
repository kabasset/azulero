# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astroquery.simbad import Simbad
import requests
import sys


def object_radec(name: str):
    res = Simbad().query_object(name)
    assert len(res) > 0, f"Object not found: {name}"
    assert len(res) < 2, f"Several objects found: {name}"
    return float(res[0]["ra"]), float(res[0]["dec"])


def radec_tiles(radec: tuple, dsr: str = "DR1_R1"):
    epsilon = 1e-8  # FIXME param?
    query = {
        "project": "EUCLID",
        "class_name": "DpdMerTile",
        # "Header.DataSetRelease": dsr,
        "spatial_query": f"CONTAINS BOUNDINGBOX({radec[0]} {radec[1]}, {radec[0]+epsilon} {radec[1]+epsilon}) REVERSE",
        "fields": "Data.TileIndex:Data.RaCen:Data.DecCen",
    }
    lines = (
        requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        .text.replace('"', "")
        .split()
    )
    tiles = {}
    for l in lines[1:]:
        index, ra, dec = l.split(",")
        tiles[index] = (ra, dec)
    return tiles


def object_tiles(name: str):
    return radec_tiles(object_radec(name))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"{arg}: {object_radec(arg)}")
        tiles = object_tiles(arg)
        if len(tiles) == 0:
            print("- WARNING: No tile found.")
        for t in tiles:
            print(f"- {t}: {tiles[t]}")
