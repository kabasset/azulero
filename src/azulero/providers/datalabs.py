# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from azulero.providers.sas import SAS
from azulero.providers.filesystem import LocalDataStore


class Datalabs(LocalDataStore):

    def __init__(self, sas: SAS):
        self._sas = sas

    def _datafile_path(self, name):
        q = f"SELECT file_name, datalabs_path FROM sedm.mosaic_product WHERE file_name='{name}'"
        res = self._sas.get_table(q)[0]
        return Path(res["datalabs_path"]) / res["file_name"]  # type: ignore
