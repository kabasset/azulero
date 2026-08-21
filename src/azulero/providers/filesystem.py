# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from astropy.coordinates import SkyCoord
from pathlib import Path

from azulero.providers import abc
from azulero.providers.cutout import local_cutout
from azulero.providers.tiling import Target, Tile


class LocalDataStore(abc.DataStoreWithCutoutService):

    def download_datafile(self, name: str, path: Path):
        path.symlink_to(self._datafile_path(name))

    def download_cutout(self, name: str, path: Path, target: Target):
        assert target.coord is not None
        assert target.radius is not None
        local_cutout(
            self._datafile_path(name),
            path,
            target.coord,
            target.radius,
        )

    @abstractmethod
    def _datafile_path(self, name) -> Path:
        pass


class LocalFileSystem(LocalDataStore, abc.SpatialProductDatabase):

    def __init__(self, provider: abc.SpatialProductDatabase, template: str):
        self.provider = provider
        self.template = template

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]) -> list[Tile]:
        return self.provider.query_radec_tiles(radec, dsrs)

    def query_tile_datafiles(self, tile: Tile) -> dict[str, str]:
        datafiles = self.provider.query_tile_datafiles(tile)
        render = lambda f, c: self.template.format(
            tile=tile.index,
            dsr=tile.dsr,
            mode=tile.mode,
            channel=c,
            filename=f,
        )
        res = {render(f, c): c for f, c in datafiles.items()}
        return res

    def _datafile_path(self, name: str) -> Path:
        return Path(name)
