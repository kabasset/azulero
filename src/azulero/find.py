# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.coordinates import SkyCoord
from dataclasses import dataclass
import json
from pathlib import Path
from shapely import geometry

from azulero.image import io
from azulero.tools.timing import Timer


def add_parser(subparsers, help):

    parser = subparsers.add_parser(
        "find",
        help=help,
        description=(
            "Find object coordinates and "
            "(a) intersecting tiles from a Geojson catalog of tiles, or "
            "(b) image coordinates in pixels from a WCS file."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "objects",
        type=str,
        nargs="*",
        help="Object names.",
    )
    parser.add_argument(
        "--radec",
        type=str,
        nargs=2,
        default=[],
        action="append",
        metavar=("RA", "DEC"),
        help="Coordinates (this option can be specified several times).",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--tiling",
        type=str,
        default=None,
        metavar="PATH",
        help="Geojson file which lists existing tiles and their metadata",
    )
    group.add_argument(
        "--wcs",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to the WCS parameters as a FITS or YAML file.",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=100,
        metavar="PIXELS",
        help="To define an image crop, with option --wcs, the radius of the crop region.",
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

    timer = Timer()
    tiling = None
    wcs = None
    if args.tiling:
        filename = Path(args.workspace) / args.tiling
        print(f"Load tiling: {args.tiling}")
        tiling = Tiling(filename)
        timer.tic_log()
    elif args.wcs:
        print(f"Load WCS: {args.wcs}")
        wcs = io.read_wcs(Path(args.workspace), args.wcs)
    else:
        print("WARNING: No tiling or WCS file given; will only find coordinates.")

    print()

    objects = args.objects + [SkyCoord(*rd, unit="deg") for rd in args.radec]
    for o in objects:
        if isinstance(o, str):
            print(o)
            o = SkyCoord.from_name(o)
            print(f"- Coordinates: {o.ra:.2f}, {o.dec:.2f}")
        else:
            print(f"{o.ra.degree} {o.dec.degree}")
        if tiling is not None:
            tiles = tiling(o)
            for t in tiles:
                print(f"- {t}")
            timer.tic_log()
            if len(tiles) > 0:
                print(f"\nYou may now run:")
                print(
                    f"\nazul --workspace {args.workspace} retrieve {' '.join(str(t.index) for t in tiles)}\n"
                )
            else:
                print("\nWARNING: No tile found.\n")
        elif wcs is not None:
            x, y = wcs.world_to_pixel(o)
            print(f"- x = {x:.1f} px (0-based from left)")
            print(f"- y = {y:.1f} px (0-based from bottom)")
            print(f"\nYou may now run:")
            wcs_file = Path(args.workspace) / args.wcs
            tiledir = wcs_file.parent
            workspace = tiledir.parent
            tile = tiledir.name
            radius = 100  # FIXME option
            print(
                f"\nazul --workspace {workspace} process "
                f"{tile}[{int(y)-radius}:{int(y)+radius},{int(x)-radius}:{int(x)+radius}]"
                f"\n"
            )
            pass
