# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from azulero.providers.cutout import local_cutout
from azulero.providers.tiling import Target
from azulero.providers.sas import SAS


class Datalabs:

    def __init__(self, sas: SAS):
        self._sas = sas

    def download_datafile(self, name: str, path: Path):
        path.symlink_to(self._datafile_path(name))

    def download_cutout(
        self,
        name: str,
        path: Path,
        target: Target,
    ) -> Path:
        return local_cutout(
            self._datafile_path(name), path, target.coord, target.radius
        )

    def _datafile_path(self, name):
        q = f"SELECT file_name, datalabs_path FROM sedm.mosaic_product WHERE file_name='{name}'"
        res = self._sas.get_table(q)[0]
        return Path(res["datalabs_path"]) / res["file_name"]  # type: ignore
