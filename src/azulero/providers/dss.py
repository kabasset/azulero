# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import gzip
from io import BytesIO
from pathlib import Path
import requests

from azulero.providers.tiling import Tile


class DSS(object):

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
