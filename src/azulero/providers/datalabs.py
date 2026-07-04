# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle, SkyCoord
from astroquery.esa.euclid import EuclidClass
import contextlib  # intercept astroquery prints
from dataclasses import dataclass
from io import StringIO
import netrc

from azulero.providers.tiling import Tile, Target
from azulero.providers.sas import SAS
from azulero.providers.cutout import local_cutout


class Datalabs:

    def __init__(self, env):
        self._sas = SAS(env)
        # Implementation detail: we use AstroQuery even for Datalabs
        # as proposed in Datalabs' Getting Started notebook

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        return self._sas.query_tiles(radec, dsrs)

    def query_datafiles(self, tile: str, dsr: str):
        return self._sas.query_datafiles(radec, dsrs)

    def download_datafile(self, name: str, path: Path):
        path.symlink_to(self._datafile_path(name))

    def download_cutout(
        self,
        name: str,
        path: Path,
        target: Target,
        radius: Angle,
    ) -> Path:
        return local_cutout(self._datafile_path(name), path, target.coord, radius)

    def _datafile_path(self, name):
        q = f"SELECT file_name, datalabs_path FROM sedm.mosaic_product WHERE file_name='{name}'"
        res = self.euclid.launch_job(q).get_results()[0]  # type: ignore
        return Path(res["datalabs_path"]) / res["file_name"]  # type: ignore
