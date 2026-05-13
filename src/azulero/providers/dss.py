# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
from dataclasses import dataclass
import gzip
from io import BytesIO
import json
from pathlib import Path
import requests
from shapely import geometry


@dataclass(frozen=True)
class Tile(object):  # FIXME duplication
    index: str
    mode: str
    dsr: str
    distance: float

    def __str__(self) -> str:
        return f"{self.mode}: {self.index} ({self.dsr}); distance: {self.distance:.2f}°"


class DSS(object):

    def read_tiling(self, tiling: Path | str):
        with open(tiling) as f:
            self.tiles = json.load(f)["features"]
        return self.tiles

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        self.read_tiling("DpdMerFinalCatalog.geojson")  # FIXME
        point = geometry.Point(radec.ra.degree, radec.dec.degree)
        res = []
        for tile in self.tiles:
            polygon = geometry.shape(tile["geometry"])
            if polygon.contains(point):
                index = tile["properties"]["TileIndex"]
                mode = tile["properties"]["ProcessingMode"]
                dsr = tile["properties"]["DatasetRelease"]
                center = polygon.centroid
                distance = center.distance(point)
                if distance < 1 and dsr in dsrs:
                    res.append(Tile(index, mode, dsr, distance))
        return sorted(
            sorted(
                set(res),
                key=lambda t: t.distance,
            ),
            key=lambda t: t.mode,
        )  # FIXME sorting to retrieve.py to be applied to all providers

    def query_datafiles(self, tile, dsr):

        query = {
            "project": "EUCLID",
            "class_name": "DpdMerBksMosaic",
            "Data.TileIndex": tile,
            "Header.DataSetRelease": dsr,
            "fields": "Data.DataStorage.DataContainer.FileName:Data.Filter.Name",
        }

        r = requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        r.raise_for_status()

        lines = r.text.replace('"', "").split()
        datafiles = {}
        for l in lines:
            if "VIS" in l or "NIR" in l:  # FIXME handled by caller
                file_name, filter_name = l.split(",")
                datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name, path):

        r = requests.get(f"https://euclidsoc.esac.esa.int/{name}")
        r.raise_for_status()

        with gzip.GzipFile(fileobj=BytesIO(r.content)) as f:
            content = f.read()
        with open(path, "wb") as f:
            f.write(content)
