# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astroquery.simbad import Simbad
from dataclasses import dataclass
import json
import pathlib
import requests
from shapely import geometry

from azulero.timing import Timer


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "find",
        help="Find the tiles which contain objects.",
        description="Find object coordinates and intersecting tiles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "objects",
        type=str,
        nargs="+",
        metavar="NAMEs",
        help="Space-separated list of tile indices.",
    )
    parser.add_argument(
        "--tiling",
        type=str,
        default="DpdMerFinalCatalog.geojson",
        metavar="FILENAME",
        help="Geojson file which lists existing tiles and their metadata",
    )

    parser.set_defaults(func=run)


def object_radec(name: str):
    # TODO use astropy's from_name()
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
                    # FIXME avoid overwriting dsr
        if len(matches) == 0:
            print("- WARNING: No tile found.")
            return []
        return sorted(matches.values(), key=lambda t: t.distance)


def run(args):

    print()

    timer = Timer()
    tiling = Tiling(pathlib.Path(args.workspace) / args.tiling)
    timer.tic_print()

    print()
    for object in args.objects:
        print(f"{object}")
        radec = object_radec(object)
        print(f"- Coordinates: {radec[0]:.2f}, {radec[1]:.2f}")
        tiles = tiling(radec)
        for t in tiles:
            print(f"- {t}")
        timer.tic_print()
        if len(tiles) > 0:
            print(f"\nYou may now run:")
            print(
                f"\nazul --workspace {args.workspace} retrieve {' '.join(str(t.index) for t in tiles)}\n"
            )
