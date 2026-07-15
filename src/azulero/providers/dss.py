# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
import csv
import gzip
from io import BytesIO, StringIO
from pathlib import Path
import requests
from shapely import geometry

from azulero.providers.tiling import Tile, query_geotiles


class DSS(object):

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        tiles = []
        for d in dsrs:
            tiles += self._query_dsr_tiles(radec, d)  # FIXME
        return tiles

    def _query_dsr_tiles(self, radec: SkyCoord, dsr: str):
        point = geometry.Point(radec.ra.degree, radec.dec.degree)  # type: ignore
        ring = self._query_tile_ring(radec, dsr).values()
        return query_geotiles(radec, ring)

    def _query_tile_ring(self, radec: SkyCoord, dsr: str):
        root = "https://eas-dps-rest-ops.esac.esa.int/REST"
        dsr_query = f"Header.DataSetRelease={dsr}"
        dec_deg: float = radec.dec.degree  # type: ignore
        margin_deg = (
            32.0 / 60.0 / 2
        )  # FIXME this is the default WIDE tile height, not the max
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
            f"{root}?project=EUCLID&class_name=DpdMerBksMosaic&{dsr_query}&{dec_query}&fields={fields_text}"
        )
        r.raise_for_status()
        return self._parse_geotiles(r.text)

    def _parse_geotiles(self, text: str):
        """
        Parse tiles in geojson format from DPS response.
        """
        tiles = {}
        reader = csv.reader(StringIO(text))
        next(reader)
        for row in reader:
            product, index, dsr, mode, ra, dec = row
            if product not in tiles:
                properties = {
                    "TileIndex": index,
                    "DatasetRelease": dsr,
                    "ProcessingMode": mode,
                }
                tiles[product] = {
                    "properties": properties,
                    "geometry": {"type": "Polygon", "coordinates": [[]]},
                }
            tiles[product]["geometry"]["coordinates"][0].append([float(ra), float(dec)])
        return tiles

    def query_datafiles(self, tile: Tile, dsr: str):

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

    def download_datafile(self, name: str, path: Path):

        r = requests.get(f"https://euclidsoc.esac.esa.int/{name}")
        r.raise_for_status()

        with gzip.GzipFile(fileobj=BytesIO(r.content)) as f:
            content = f.read()
        with open(path, "wb") as f:
            f.write(content)
        return path
