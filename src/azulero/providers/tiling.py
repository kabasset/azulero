# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable

from astropy import units
from astropy.coordinates import Angle, SkyCoord
from dataclasses import dataclass, field
import json
from pathlib import Path

from azulero.providers.spherical import ConvexSphericalPolygon, radec_to_xyz
from azulero.tools.workspace import Workspace


@dataclass(frozen=True)
class Tile(object):
    index: str = ""
    mode: str = "UNKNOWN"
    dsr: str = "UNKNOWN"
    distance: float = 0.0  # FIXME Angle

    def __str__(self) -> str:
        res = f"{self.index}: dataset {self.dsr}, survey {self.mode}"
        if self.distance > 0:
            res += f" (distance: {self.distance:.2f}°)"
        return res


@dataclass(frozen=True)
class Target:

    name: str = ""
    tile: Tile = Tile()
    coord: SkyCoord | None = field(default=None, compare=False)
    radius: Angle | None = field(default=None, compare=False)

    def tiledir(self, ios: Workspace) -> Path:
        return Path(
            ios.output_template.format(
                workspace=ios.workspace, tile=self.tile, target=""
            )
        )

    def workdir(self, ios: Workspace) -> Path:

        if self.name == self.tile.index:
            target = ""
        else:
            target = self.name

        unit_str = {units.degree: "d", units.arcminute: "m", units.arcsecond: "s"}
        if self.radius is None:
            radius = ""
        elif self.radius.unit in unit_str:
            radius = f"r{self.radius.value}{unit_str[self.radius.unit]}"  # type: ignore
        else:
            radius = (
                f"r{float(self.radius / units.arcsecond)}{unit_str[units.arcsecond]}"
            )

        workdir = ios.output_template.format(
            workspace=ios.workspace,
            tile=self.tile.index,
            target=target,
            dsr=self.tile.dsr,
            radius=radius,
        )
        return Path(workdir)


class Tiling:

    def __init__(self, filename: Path):
        with open(filename) as f:
            self.tiles = json.load(f)["features"]
        # FIXME instantiate ConvexPolygon here

    def query_tile_attributes(self, index: str) -> list[Tile]:
        return [
            Tile(
                index,
                t["properties"]["ProcessingMode"],
                t["properties"]["DatasetRelease"],
            )
            for t in self.tiles
            if t["properties"]["TileIndex"] == index
        ]

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]):
        return query_geotiles(radec, self.tiles, dsrs)


def query_geotiles(radec: SkyCoord, geotiles: Iterable, dsrs: list[str] | None = None):
    res = []
    p = radec_to_xyz(radec.ra, radec.dec)
    for tile in geotiles:
        polygon = ConvexSphericalPolygon.from_geojson(tile["geometry"])
        # FIXME use ConvexPolygon
        if p in polygon:
            index = tile["properties"]["TileIndex"]
            mode = tile["properties"]["ProcessingMode"]
            dsr = tile["properties"]["DatasetRelease"]
            distance = polygon.centroid.separation(radec).value
            if distance < 1 and (dsrs is None or dsr in dsrs):
                res.append(Tile(index, mode, dsr, distance))
    return res
