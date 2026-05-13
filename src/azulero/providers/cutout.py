# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle

from azulero.providers import tiling


class LocalCutout:
    """
    Decorator class which adds local cutout service to a data provider without a cutout service.
    The datafiles are downloaded in full in the tile folder,
    and cutouts are extracted from them and written to the workdir.
    """

    def __init__(self, provider):
        self.provider = provider

    def download_datafiles(
        self,
        name: str,
        path: Path,
        target: tiling.Target | None = None,
        radius: Angle | None = None,
    ):
        if target is None or radius is None:
            return self.provider.download_datafile(name, path)
        tiledir = path.parent  # FIXME resolve tile folder
        tile = self.provider.download_datafiles(name, tiledir)
        return self._cut(tile, path)

    def _cut(self, tile: Path, cutout: Path):
        # FIXME
        return cutout
