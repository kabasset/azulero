# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import SkyCoord
from typing import Protocol, runtime_checkable

from azulero.providers.tiling import Tile, Target


@runtime_checkable
class ProductDatabase(Protocol):  # TODO rename as FileDatabase?
    """
    Abstract base class for product databases.
    """

    def query_tile_datafiles(self, tile: Tile) -> dict[str, str]:
        """
        Get the list of datafiles and associated channels from a tile.

        Returns:
            A datafile-channel dictionary.
        """
        ...


@runtime_checkable
class TilingDatabase(Protocol):
    """
    Abstract base class for spatial databases.
    """

    def query_tile_attributes(self, index: str) -> list[Tile]:
        """
        Get the list of tiles with given index.
        """
        ...

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]) -> list[Tile]:
        """
        Get the list of tiles which contain a given RA/Dec.

        Args:
            radec: The target coordinate.
            dsrs: The ordered list of Dataset Release names to look for.
        """
        ...


@runtime_checkable
class DataStore(Protocol):
    """
    Abstract base class for data stores.
    """

    def download_datafile(self, name: str, path: Path):
        """
        Download and decompress a datafile.

        Args:
            name: The name of the datafile in the database.
            path: The local destination path.
        """
        ...


@runtime_checkable
class CutoutService(Protocol):
    """
    Abstract base class for cutout services.
    """

    def download_cutout(self, name: str, path: Path, target: Target):
        """
        Download a cutout.

        Args:
            name: The name of the datafile in the database.
            path: The local destination path.
            target: The cutout specification.
        """
        ...


@runtime_checkable
class DataProvider(ProductDatabase, DataStore, Protocol):
    """
    Product database with a data store.
    """

    ...


@runtime_checkable
class CutoutStore(DataStore, CutoutService, Protocol):
    """
    Data store with a cutout service.
    """

    ...
