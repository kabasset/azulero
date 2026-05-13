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
        point = geometry.Point(radec.ra.degree, radec.dec.degree)
        res = []
        for tile in tiles:
            polygon = geometry.shape(tile["geometry"])
            if polygon.contains(point):
                index = tile["properties"]["TileIndex"]
                mode = tile["properties"]["ProcessingMode"]
                dsr = tile["properties"]["DatasetRelease"]
                center = polygon.centroid
                distance = center.distance(point)
                if distance < 1 and dsr in dsrs:
                    res.append(Tile(index, mode, dsr, distance))
        return res
