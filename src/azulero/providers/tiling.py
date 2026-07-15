# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
from dataclasses import dataclass, field
import json
from pathlib import Path
from shapely import geometry

from azulero.tools.workspace import Workspace


@dataclass(frozen=True)
class Target:

    name: str
    tile: str
    coord: SkyCoord | None = field(default=None, compare=False)

    def tiledir(self, ios: Workspace) -> Path:
        return Path(
            ios.output_template.format(
                workspace=ios.workspace, tile=self.tile, target=""
            )
        )

    def workdir(self, ios: Workspace) -> Path:
        target = "" if self.name == self.tile else self.name
        workdir = ios.output_template.format(
            workspace=ios.workspace, tile=self.tile, target=target
        )
        return Path(workdir)


@dataclass(frozen=True)
class Tile(object):
    index: str
    mode: str
    dsr: str
    distance: float

    def __str__(self) -> str:
        return f"{self.mode}: {self.index} ({self.dsr}); distance: {self.distance:.2f}°"


class Tiling:

    def __init__(self, filename: Path):
        self.filename = filename

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        with open(self.filename) as f:
            tiles = json.load(f)["features"]
        return query_geotiles(radec, tiles, dsrs)


def query_geotiles(radec: SkyCoord, geotiles: list, dsrs: list[str] | None = None):
    point = geometry.Point(radec.ra.degree, radec.dec.degree)  # type: ignore
    res = []
    for tile in geotiles:
        polygon = geometry.shape(tile["geometry"])
        if polygon.contains(point):
            # FIXME use JC's code for spherical geometry
            index = tile["properties"]["TileIndex"]
            mode = tile["properties"]["ProcessingMode"]
            dsr = tile["properties"]["DatasetRelease"]
            center = SkyCoord(ra=polygon.centroid.x, dec=polygon.centroid.y, unit="deg")
            distance = center.separation(radec).value
            if distance < 1 and (dsrs is None or dsr in dsrs):
                res.append(Tile(index, mode, dsr, distance))
    return res
