# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.coordinates import SkyCoord
from dataclasses import dataclass
import json
import pathlib
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
        nargs="*",
        metavar="NAMES",
        help="Object names.",
    )
    parser.add_argument(
        "--radec",
        type=str,
        nargs=2,
        default=[],
        action="append",
        metavar=["RA", "DEC"],
        help="Coordinates (this option can be specified several times).",
    )
    parser.add_argument(
        "--tiling",
        type=str,
        default="DpdMerFinalCatalog.geojson",
        metavar="FILENAME",
        help="Geojson file which lists existing tiles and their metadata",
    )

    parser.set_defaults(func=run)


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

    def __call__(self, coord: SkyCoord):
        matches = {}
        point = geometry.Point(coord.ra.degree, coord.dec.degree)
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
        return sorted(matches.values(), key=lambda t: t.distance)


def run(args):

    print()

    timer = Timer()
    tiling = Tiling(pathlib.Path(args.workspace) / args.tiling)
    timer.tic_print()

    print()

    objects = args.objects + [SkyCoord(*rd, unit="deg") for rd in args.radec]
    for coord in objects:
        if isinstance(coord, str):
            print(coord)
            coord = SkyCoord.from_name(coord)
            print(f"- Coordinates: {coord.ra:.2f}, {coord.dec:.2f}")
        else:
            print(f"{coord.ra.degree} {coord.dec.degree}")
        tiles = tiling(coord)
        for t in tiles:
            print(f"- {t}")
        timer.tic_print()
        if len(tiles) > 0:
            print(f"\nYou may now run:")
            print(
                f"\nazul --workspace {args.workspace} retrieve {' '.join(str(t.index) for t in tiles)}\n"
            )
        else:
            print("\nWARNING: No tile found.\n")
