# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable

from astropy.coordinates import SkyCoord
import csv
import gzip
from io import BytesIO, StringIO
from pathlib import Path
import requests

from azulero.providers.tiling import Tile
from azulero.providers.spherical import ConvexPolygon, radec_to_xyz
from azulero.tools.messaging import logger
from azulero.tools.secret import Auth


class Query:

    def __init__(self, dpd):
        self.params = []
        self["project"] = "EUCLID"
        self["class_name"] = dpd
        self["Header.ManualValidationStatus"] = {"!=": "INVALID"}

    def _append(self, params, key, op, value):
        params += [f"{key}{op}{value}"]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            for op, v in value.items():
                self._append(self.params, key, op, v)
        else:
            self._append(self.params, key, "=", value)

    def __call__(self, *fields) -> str:
        params = ["fields=" + ":".join(fields)]
        return "&".join(self.params + params)


class DSS:

    def __init__(self, user: str | None):
        auth = Auth("euclidsoc.esac.esa.int", user)
        self.__auth = requests.auth.HTTPBasicAuth(auth.user, auth.password.value)  # type: ignore

    def _query(self, q: str):
        url = f"https://eas-dps-rest-ops.esac.esa.int/REST?{q}"
        logger.debug(url)
        r = requests.get(
            url,
            auth=self.__auth,
        )
        r.raise_for_status()
        reader = csv.reader(StringIO(r.text))
        next(reader)
        return reader

    def query_tile_attributes(self, index: str) -> list[Tile]:
        query = Query("DpdMerBksMosaic")
        query["Data.TileIndex"] = index
        q = query("Data.ProcessingMode", "Header.DataSetRelease")
        return [Tile(index, row[0], row[1]) for row in self._query(q)]

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]):
        ring = self._query_ring_footprints(radec)
        res = []
        p = radec_to_xyz(radec.ra, radec.dec)
        for tile in ring.values():
            polygon = ConvexPolygon(tile["ra"], tile["dec"])
            if p in polygon:
                distance = polygon.centroid.separation(radec).value
                res += [
                    Tile(
                        tile["index"],
                        tile["mode"],
                        attr.dsr,
                        distance,
                    )
                    for attr in self.query_tile_attributes(tile["index"])
                    if attr.dsr in dsrs
                ]
                # TODO Find a faster way of getting the DSR.
        return res

    def _query_ring_footprints(self, radec: SkyCoord) -> dict:
        dec_deg: float = radec.dec.degree  # type: ignore
        # Regarding the max height deviation of a tile, Martin Kuemmel wrote in Slack:
        # The papers (Q1 and DR1) quote something like 5%. [...]
        # The max width and height is 39.6' and 38.4', respectively. That would be rather 10% in each direction.
        margin_deg = 38.4 / 60 / 2
        query = Query("DpdMerTile")
        query["Data.DecCen"] = {">": dec_deg - margin_deg, "<": dec_deg + margin_deg}
        q = query(
            "Header.ProductId.LimitedString",
            "Data.TileIndex",
            "Data.TileUseCase",
            "Data.OuterSpatialFootprint.Polygon.Vertex.C1",  # RA
            "Data.OuterSpatialFootprint.Polygon.Vertex.C2",  # Dec
        )
        reader = self._query(q)
        return self._parse_tiles(reader)

    def _parse_tiles(self, reader: Iterable[list[str]]) -> dict:
        tiles = {}
        for product, index, mode, ra, dec in reader:
            if product not in tiles:
                tiles[product] = {
                    "index": index,
                    "mode": mode,
                    "dsr": "UNKNOWN",
                    "ra": [],
                    "dec": [],
                }
            tiles[product]["ra"].append(float(ra))
            tiles[product]["dec"].append(float(dec))
        return tiles

    def query_tile_datafiles(self, tile: Tile) -> dict[str, str]:

        query = Query("DpdMerBksMosaic")
        query["Data.TileIndex"] = tile.index
        query["Header.DataSetRelease"] = tile.dsr
        query["allow_array"] = True
        q = query("Data.DataStorage.DataContainer.FileName", "Data.Filter.Name")
        rows = self._query(q)

        datafiles = {}
        for file_name, filter_name in rows:
            datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name: str, path: Path):

        r = requests.get(f"https://euclidsoc.esac.esa.int/{name}", auth=self.__auth)
        r.raise_for_status()

        with gzip.GzipFile(fileobj=BytesIO(r.content)) as f:
            content = f.read()
        with open(path, "wb") as f:
            f.write(content)
