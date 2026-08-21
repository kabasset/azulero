# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
from astropy.coordinates import Angle, SkyCoord
from pathlib import Path

from typing import Callable, Iterable

from azulero.providers import dss, protocol, sas, tiling, cutout, datalabs, filesystem
from azulero.tools import parsing
from azulero.tools.messaging import logger
from azulero.tools.retry import retry

product_databases: dict[str, Callable[[str], protocol.DataProvider]] = {
    "pdr": lambda user: sas.SAS("PDR", user),
    "idr": lambda user: sas.SAS("IDR", user),
    "otf": lambda user: sas.SAS("OTF", user),
    "dss": lambda user: dss.DSS(user),  # TODO enable DSS selection
}

data_stores: dict[str, Callable[[sas.SAS], protocol.CutoutStore]] = {
    "labs": lambda provider: datalabs.Datalabs(provider),
    # TODO accept other DBs than SAS?
}


class DataProvider:
    """
    Data provider factory which implements all services,
    possibly using surrogate approaches when the service is not natively supported.

    The class selects the different service implementations based on the construction arguments.
    The service implementations are wrapped with logging and retrying.

    Args:
        name: The data provider name.
        user: The data provider user name.
        data_store: The data store name or path template.
        tiling_file: The tiling Geojson file, for optimization purpose.
    """

    product_db: protocol.DataProvider
    spatial_db: protocol.SpatialDatabase
    data_store: protocol.CutoutStore

    def __init__(
        self,
        name: str,
        user: str | None = None,
        data_store: str | None = None,
        tiling_file: Path | None = None,
    ):
        self.product_db = product_databases[name.lower()](user)
        if tiling_file is None:
            assert isinstance(self.product_db, protocol.SpatialDatabase)
            self.spatial_db = self.product_db
        else:
            logger.bullet(f"Enable local tiling: {tiling_file}")
            self.spatial_db = tiling.Tiling(tiling_file)
        if data_store:
            logger.bullet(f"Enable local data store: {data_store}")
            if data_store in data_stores:
                assert isinstance(self.product_db, sas.SAS)  # TODO accept other DBs?
                self.data_store = data_stores[data_store](self.product_db)
            else:
                self.product_db = filesystem.LocalFileSystem(
                    self.product_db, data_store
                )
                self.data_store = self.product_db
        elif isinstance(self.product_db, protocol.CutoutStore):
            logger.bullet(f"Enable distant cutout service.")
            self.data_store = self.product_db
        else:
            logger.bullet(
                "No distant cutout service available. Fall back to local cutout."
            )
            assert isinstance(self.product_db, protocol.DataStore)
            self.data_store = cutout.LocalCutout(self.product_db)

    def query_target_tiles(
        self,
        dsrs: list[str],
        modes: list[str],
        radius: Angle | None,
        target: str,
    ) -> list[tiling.Target]:
        """
        Query the list of tiles for a given target, which may be a tile index, coordinates or object name.

        Args:
            dsrs: The ordered list of dataset releases.
            modes: The ordered list of processing modes.
            radius: The global radius.
            target: The target name.

        Returns:
            The list of target attributes.
        """

        if target.isdigit():
            logger.info(f"Tile: {target}")
            tiles = self.query_tile_attributes(target, dsrs, modes)
            return [tiling.Target(target, t) for t in tiles]

        t, r = parsing.parse_target(target, radius, otype=str)
        assert r is None or isinstance(r, Angle)
        if "," in t:
            logger.info(f"Coordinates: {t}")
            ra, dec = t.split(",")
            radec = SkyCoord(ra, dec, unit="deg")
        else:
            logger.info(f"Named object: {t}")
            radec = SkyCoord.from_name(t, parse=True)
            if radec.ra is None or radec.dec is None:
                logger.error(f"Cannot find object: {t}")
                return []
            logger.bullet(
                f"Coordinates: {radec.ra.degree:.2f}° {radec.dec.degree:.2f}°"
            )

        return self.query_radec_tiles(t, radec, r, dsrs, modes)

    def query_tile_attributes(
        self, index: str, dsrs: list[str], modes: list[str]
    ) -> list[tiling.Tile]:
        """
        Get the list of tiles with a given index.
        """

        # if len(dsrs) == 1:
        #     return [tiling.Tile(index)]

        @retry(logger=logger, default=[])
        def retry_query():
            return self.spatial_db.query_tile_attributes(index)

        tiles = self.sort_tiles(retry_query(), dsrs, modes)
        for t in tiles:
            logger.bullet(f"{t}")
        return tiles

    def query_radec_tiles(
        self,
        target: str,
        radec: SkyCoord,
        radius: Angle | None,
        dsrs: list[str],
        modes: list[str],
    ) -> list[tiling.Target]:
        """
        Query the list of tiles which contain a given RA/dec coordinates.

        Args:
            radec: The target coordinates.
            radius: The target radius.
            dsrs: The ordered list of dataset releases.
            modes: The ordered list of processing modes.

        Returns:
            The list of target attributes.
        """

        @retry(logger=logger, default=[])
        def retry_query():
            return self.spatial_db.query_radec_tiles(radec, dsrs)

        tiles = self.sort_tiles(retry_query(), dsrs, modes)

        for t in tiles:
            logger.bullet(f"Tile: {t}")
        targets = [tiling.Target(target, tile, radec, radius) for tile in tiles]
        if len(targets) == 0:
            logger.warning("No tile found!")
        return list(targets)

    def sort_tiles(
        self,
        tiles: list[tiling.Tile],
        dsrs: list[str],
        modes: list[str],
    ) -> list[tiling.Tile]:
        """
        Sort tiles according to given Dataset Release and processing mode orderings.
        """
        dsrs = dsrs + ["UNKNOWN"]
        res = {t for t in tiles if (t.dsr in dsrs and t.mode in modes)}
        res = sorted(res, key=lambda t: t.distance)
        res = sorted(res, key=lambda t: dsrs.index(t.dsr))
        res = sorted(res, key=lambda t: modes.index(t.mode))

        # We want a unique tile per index, while keeping them in order,
        # which means, for each index, keeping the tile with best DSR.
        # We reverse the list twice so that better tiles override others at dict creation.
        d = {t.index: t for t in reversed(res)}
        return list(reversed(d.values()))

    def query_tile_datafiles(self, tile: tiling.Tile):
        """
        Query the datafiles of a tile.

        Args:
            tile: The tile index.
            dsr: The Dataset Release name.
        """

        @retry(logger=logger, default=[])
        def retry_query():
            return self.product_db.query_tile_datafiles(tile)

        datafiles = retry_query()
        datafiles = {
            file: filter
            for file, filter in datafiles.items()
            if "VIS" in filter or "NIR" in filter
        }
        if len(datafiles) == 0:
            logger.warning("No datafile found.")

        for f in datafiles:
            logger.bullet(f"[{datafiles[f]}] {f}")
        return datafiles

    def download_datafiles(
        self,
        datafiles: Iterable[str],
        workdir: Path,
        target: tiling.Target,
        overwrite: bool,
    ) -> list[Path]:
        """
        Download and decompress datafiles.

        Args:
            datafiles: The list of datafile names.
            workdir: The destination directory.
            target: The target attributes.
            overwrite: Boolean flag to enable or disable overwriting.
        """

        paths = [workdir / Path(n).name.removesuffix(".gz") for n in datafiles]
        for name, path in zip(datafiles, paths):  # TODO parallelize?
            if path.is_file() and not overwrite:
                logger.bullet(f"File already exists; skip: {path.name}")
            else:
                logger.bullet(f"{path.name}")
                if path.is_file():
                    logger.warning(f"Existing file will be overwritten: {path.name}")

                @retry(logger=logger)
                def retry_download():
                    if target.radius is None:
                        self.data_store.download_datafile(name, path)
                    else:
                        self.data_store.download_cutout(name, path, target)
                    with fits.open(path):
                        return

                retry_download()
        return paths
