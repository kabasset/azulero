# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord
import gzip
from io import BytesIO
from pathlib import Path
import requests

from azulero.providers.tiling import Tile


def tile(res, target):
    index, ra, dec, dsr, mode = res.split(",")
    center = SkyCoord(ra, dec, unit="deg", frame="icrs")
    distance = center.separation(target).value
    return Tile(
        index,
        mode,
        dsr,
        distance,
    )


class DSS(object):

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        root = "https://eas-dps-rest-ops.esac.esa.int/REST"
        dsrs_text = ",".join("'" + d + "'" for d in dsrs)
        dsr_query = f"Header.DataSetRelease+IN({dsrs_text})"
        dec_deg = radec.ra.value  # FIXME degrees
        dec_query = f"Data.WCS.CRVAL2+BETWEEN({dec_deg - 0.51},{dec_deg + 0.51})"
        select_text = "Data.TileIndex:Data.WCS.CRVAL1:Data.WCS.CRVAL2:Header.DataSetRelease:Data.ProcessingMode"
        r = requests.get(
            f"{root}?project=EUCLID&class_name=DpdMerBksMosaic&{dsr_query}&{dec_query}&fields={select_text}"
        )
        r.raise_for_status()
        print(r.text)
        lines = r.text.replace('"', "").split()
        return [tile(l, radec) for l in lines]

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
