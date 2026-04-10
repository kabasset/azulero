# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import requests


class SAS(object):

    def query_datafiles(self, tile, dsr):
        adql = (
            f"SELECT TOP 50 file_name, filter_name FROM sedm.mosaic_product"
            f" WHERE (release_name='{dsr}')"
            f" AND (category='SCIENCE')"
            f" AND (tile_index={tile})"
            f" AND (instrument_name IN ('VIS', 'NISP'))"  # FIXME handled by caller
        )
        query = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "csv",
            "QUERY": adql.replace(" ", "+"),
        }
        url = "https://eas.esac.esa.int/tap-server/tap/sync?" + "&".join(
            f"{p}={query[p]}" for p in query
        )
        r = requests.get(url)  # Cannot use params as adql characters would be escaped
        r.raise_for_status()

        lines = r.text.split()
        datafiles = {}
        for l in lines[1:]:
            file_name, filter_name = l.split(",")
            datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name, path):

        query = {"file_name": name, "release": "sedm", "RETRIEVAL_TYPE": "FILE"}
        r = requests.get(f"https://eas.esac.esa.int/sas-dd/data", query)
        r.raise_for_status()

        with open(path, "wb") as f:
            f.write(r.content)
