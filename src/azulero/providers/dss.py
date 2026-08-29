# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
import csv
import gzip
from io import BytesIO, StringIO
from pathlib import Path
import requests

from azulero.providers.tiling import Tile
from azulero.providers.spherical import (
    ConvexPolygon,
    radec_to_xyz,
)
from azulero.tools.secret import Auth


class DSS:

    def __init__(self, user: str | None):
        auth = Auth("euclidsoc.esac.esa.int", user)
        self.__auth = requests.auth.HTTPBasicAuth(auth.user, auth.password.value)  # type: ignore

    def _get(self, fields: list[str], params: dict[str, str]):
        query = {
            "project": "EUCLID",
            "class_name": "DpdMerBksMosaic",
            "fields": ":".join(fields),
        }
        query.update(params)

        r = requests.get(
            "https://eas-dps-rest-ops.esac.esa.int/REST",
            params=query,
            auth=self.__auth,
        )
        r.raise_for_status()
        lines = r.text.replace('"', "").split()
        return [l.split(",") for l in lines[1:]]

    def query_tile_attributes(self, index: str) -> list[Tile]:
        res = self._get(
            ["Data.ProcessingMode", "Header.DataSetRelease"],
            {"Data.TileIndex": index},
        )
        return [Tile(index, r[0], r[1]) for r in res]

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]):
        tiles = []
        for d in dsrs:
            tiles += self._query_dsr_tiles(radec, d)
        return tiles

    def _query_dsr_tiles(self, radec: SkyCoord, dsr: str):
        ring = self._query_tile_ring(radec, dsr).values()
        res = []
        p = radec_to_xyz(radec.ra, radec.dec)
        for tile in ring:
            polygon = ConvexPolygon(tile["ra"], tile["dec"])
            if p in polygon:
                res.append(
                    Tile(
                        tile["index"],
                        tile["mode"],
                        tile["dsr"],
                        polygon.centroid.separation(radec).value,
                    )
                )
        return res

    def _query_tile_ring(self, radec: SkyCoord, dsr: str) -> dict:
        root = "https://eas-dps-rest-ops.esac.esa.int/REST"
        dsr_query = f"Header.DataSetRelease={dsr}"
        dec_deg: float = radec.dec.degree  # type: ignore
        margin_deg = 38.4 / 60.0 / 2
        # About the max height of a tile, Martin Kuemmel says:
        # The papers (Q1 and DR1) quote something like 5%.
        # [...]
        # The max width and height is 39.6' and 38.4', respectively. That would be rather 10% in each direction.
        dec_query = f"Data.WCS.CRVAL2>{dec_deg - margin_deg}&Data.WCS.CRVAL2<{dec_deg + margin_deg}"
        fields = [
            "Header.ProductId.LimitedString",
            "Data.TileIndex",
            "Header.DataSetRelease",
            "Data.ProcessingMode",
            "Data.ImgSpatialFootprint.Polygon.Vertex.C1",  # RA
            "Data.ImgSpatialFootprint.Polygon.Vertex.C2",  # Dec
        ]
        fields_text = ":".join(fields)
        r = requests.get(
            f"{root}?project=EUCLID&class_name=DpdMerBksMosaic&{dsr_query}&{dec_query}&fields={fields_text}",
            auth=self.__auth,
        )
        r.raise_for_status()
        return self._parse_tiles(r.text)

    def _parse_tiles(self, text: str) -> dict:

        tiles = {}
        reader = csv.reader(StringIO(text))
        next(reader)

        for row in reader:
            product, index, dsr, mode, ra, dec = row
            if product not in tiles:
                tiles[product] = {
                    "index": index,
                    "mode": mode,
                    "dsr": dsr,
                    "ra": [],
                    "dec": [],
                }
            tiles[product]["ra"].append(float(ra))
            tiles[product]["dec"].append(float(dec))

        return tiles

    def query_tile_datafiles(self, tile: Tile) -> dict[str, str]:

        query = {
            "project": "EUCLID",
            "class_name": "DpdMerBksMosaic",
            "Data.TileIndex": tile.index,
            "Header.DataSetRelease": tile.dsr,
            "fields": "Data.DataStorage.DataContainer.FileName:Data.Filter.Name",
        }

        r = requests.get(
            "https://eas-dps-rest-ops.esac.esa.int/REST",
            params=query,
            auth=self.__auth,
        )
        r.raise_for_status()

        lines = r.text.replace('"', "").split()
        datafiles = {}
        for l in lines:
            if "VIS" in l or "NIR" in l:  # FIXME handled by caller
                file_name, filter_name = l.split(",")
                datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name: str, path: Path):

        r = requests.get(f"https://euclidsoc.esac.esa.int/{name}")
        # FIXME use getpass in Datalabs
        r.raise_for_status()

        with gzip.GzipFile(fileobj=BytesIO(r.content)) as f:
            content = f.read()
        with open(path, "wb") as f:
            f.write(content)
