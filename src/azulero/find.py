# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import json
from astroquery.simbad import Simbad
import requests
from shapely import geometry
import sys


def object_radec(name: str):
    res = Simbad().query_object(name)
    assert len(res) > 0, f"Object not found: {name}"
    assert len(res) < 2, f"Several objects found: {name}"
    return float(res[0]["ra"]), float(res[0]["dec"])


def radec_tiles(radec: tuple):
    epsilon = 1e-8  # FIXME param?
    query = {
        "project": "EUCLID",
        "class_name": "DpdMerBksMosaic",
        "spatial_query": f"INTERSECT(0.01,101) BOUNDINGBOX({radec[0]-epsilon} {radec[1]-epsilon}, {radec[0]+epsilon} {radec[1]+epsilon})",
        "fields": "Header.ProductId",  # "Data.TileIndex:Data.RaCen:Data.DecCen",
    }
    lines = (
        requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        .text.replace('"', "")
        .split()
    )
    print("\n".join(lines))
    tiles = {}
    for l in lines[1:]:
        index, ra, dec = l.split(",")
        tiles[index] = (ra, dec)
    return tiles


def object_tiles(name: str):
    return radec_tiles(object_radec(name))


@dataclass
class Tile(object):
    index: int
    mode: str
    dsr: str
    distance: float

    def __str__(self) -> str:
        return f"{self.mode}: {self.index} ({self.dsr}); distance: {self.distance:.2f}°"


class Tiling(object):

    def __init__(self, filename):
        print(f"Load tiling: {filename}")
        with open(filename) as f:
            self.tiles = json.load(f)["features"]
        print(f"- {len(self.tiles)} tiles loaded.")

    def __call__(self, radec: tuple):
        matches = {}
        point = geometry.Point(*radec)
        for tile in self.tiles:
            polygon = geometry.shape(tile["geometry"])
            if polygon.contains(point):
                # FIXME use astropy-region for spherical geometry
                index = tile["properties"]["TileIndex"]
                mode = tile["properties"]["ProcessingMode"]
                dsr = tile["properties"]["DatasetRelease"]
                center = polygon.centroid
                distance = center.distance(point)
                if distance < 1:
                    matches[index] = Tile(index, mode, dsr, distance)
        if len(matches) == 0:
            print("- WARNING: No tile found.")
            return []
        return sorted(matches.values(), key=lambda t: t.distance)


if __name__ == "__main__":
    tiling = Tiling("DpdMerFinalCatalog.geojson")
    for arg in sys.argv[1:]:
        print(f"\n{arg}")
        radec = object_radec(arg)
        print(f"- Coordinates: {radec[0]:.2f}, {radec[1]:.2f}")
        tiles = tiling(radec)
        for t in tiles:
            print(f"- {t}")
