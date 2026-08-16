# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.io import fits
from astropy.coordinates import Angle, SkyCoord
from pathlib import Path

from azulero.image import io
from azulero.providers import dss, sas, tiling, cutout, datalabs
from azulero.tools import parsing
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
    progress_str,
)
from azulero.tools.retry import retry
from azulero.tools.timing import Timer
from azulero.tools.workspace import Workspace

product_databases = {
    "pdr": lambda user: sas.SAS("PDR", user),
    "idr": lambda user: sas.SAS("IDR", user),
    "otf": lambda user: sas.SAS("OTF", user),
    "dss": lambda user: dss.DSS(user),  # TODO enable DSS selection
}

data_stores = {
    "labs": lambda provider: datalabs.Datalabs(provider),
}


class DataProvider:
    """
    Data provider factory which implements all services,
    possibly using surrogate approaches when the service is not natively supported.

    The class selects the different service implementations based on the construction arguments.

    Args:
        name: The data provider name.
        user: The data provider user name.
        data_store: The data store name or path template.
        tiling_file: The tiling Geojson file, for optimization purpose.
    """

    def __init__(
        self,
        name: str,
        user: str | None = None,
        data_store: str | None = None,
        tiling_file: Path | None = None,
    ):
        self.product_db = product_databases[name.lower()](user)
        self.spatial_db = (
            self.product_db if tiling_file is None else tiling.Tiling(tiling_file)
        )
        if data_store and data_store in data_stores:
            logger.bullet(f"Enable local data store: {data_store}")
            self.data_store = data_stores[data_store](self.product_db)
        elif hasattr(self.product_db, "download_cutout"):
            logger.bullet(f"Enable distant cutout service.")
            self.data_store = self.product_db
        else:
            logger.bullet("Enable local cutout service.")
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
            return [tiling.Target(target, target)]

        t, r = parsing.parse_target(target, radius, otype=str)
        if "," in t:
            logger.info(f"Coordinates: {t}")
            ra, dec = t.split(",")
            radec = SkyCoord(ra, dec, unit="deg")
        else:
            logger.info(f"Named object: {t}")
            radec = SkyCoord.from_name(t, parse=True)
            # FIXME raise/skip if .ra or .dec is None
            logger.bullet(
                f"Coordinates: {radec.ra.degree:.2f}° {radec.dec.degree:.2f}°"
            )

        return self.query_radec_tiles(t, radec, r, dsrs, modes)

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
            return self.spatial_db.query_tiles(radec, dsrs)

        tiles = self.sort_tiles(retry_query(), dsrs, modes)

        for tile in tiles:
            logger.bullet(f"Tile: {tile}")
        targets = [tiling.Target(target, tile.index, radec, radius) for tile in tiles]
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
        res = set(t for t in tiles if (t.dsr in dsrs and t.mode in modes))
        res = sorted(res, key=lambda t: t.distance)
        res = sorted(res, key=lambda t: dsrs.index(t.dsr))
        res = sorted(res, key=lambda t: modes.index(t.mode))
        return res

    def query_tile_datafiles(self, tile: str, dsr: str):
        """
        Query the datafiles of a tile.

        Args:
            tile: The tile index.
            dsr: The Dataset Release name.
        """

        @retry(logger=logger, default=[])
        def retry_query():
            return self.product_db.query_datafiles(tile, dsr)

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
        datafiles: list[str],
        workdir: Path,
        target: tiling.Target,
        overwrite: bool,
    ):
        """
        Download datafiles.

        Args:
            datafiles: The list of datafile names.
            workdir: The destination directory.
            target: The target attributes.
            overwrite: Boolean flag to enable or disable overwriting.
        """

        for name in datafiles:  # TODO parallelize?
            path = workdir / name.removesuffix(".gz")
            if path.is_file() and not overwrite:
                logger.bullet(f"File already exists; skip: {path.name}")
            else:
                logger.bullet(f"{path.name}")
                if path.is_file():
                    logger.warning(f"Existing file will be overwritten: {path.name}")

                @retry(logger=logger)
                def retry_query():
                    if target.radius is None:
                        self.data_store.download_datafile(name, path)
                    else:
                        self.data_store.download_cutout(name, path, target)
                    with fits.open(path):
                        return

                retry_query()


def add_parser(subparsers, help):

    parser = subparsers.add_parser(
        "retrieve",
        help=help,
        description="Query and download various datafiles at given positions or tile indices.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "targets",
        type=str,
        nargs="*",
        default=read_pipe_args(),
        help=(
            "Space-separated list of tile indices (e.g. 102159776), "
            "coordinates (e.g. 270.93°,67.05°), and/or object names (e.g. UGC11116). "
            "A specific cone search angle can be specified between brackets (e.g. UGC11116[r=2m]). "
            "See also option -r."
        ),
    )
    parser.add_argument(
        "--survey",
        type=str,
        default="DEEP,WIDE,UNKNOWN",
        metavar="MODES",
        help="Comma-separated list of processing modes in order of preference.",
    )
    parser.add_argument(
        "--dsr",
        type=str,
        default="DR1_R2,DR1_R1,Q1_R1",
        metavar="NAMES",
        help="Comma-separated list of data set releases in order of preference.",
    )
    parser.add_argument(
        "--from",
        type=str,
        default="idr",
        choices=product_databases.keys(),
        help="Data provider.",
    )
    parser.add_argument(
        "--user",
        type=str,
        metavar="NAME",
        help="Provider user name, in order to enable interactive password prompt.",
    )
    parser.add_argument(
        "--radius",
        "-r",
        type=Angle,
        metavar="ANGLE",
        help=(
            "Default cone search angle (if set, will retrieve cutouts instead of tiles). "
            "Overwritten by specific angles."
        ),
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        metavar="COUNT",
        help="Maximum number of tiles to be retrieved per target.",
    )
    parser.add_argument(
        "--force",
        "-f",
        type=str,
        nargs="*",
        default=None,
        metavar="FILENAMES",
        help=(
            "Force file download, overwriting existing files. "
            "A list of filenames can be specified, in which case the query step is bypassed."
        ),
    )
    parser.add_argument(
        "--query-only",
        "-q",
        type=str,
        nargs="?",
        const="files",
        default=None,
        choices=["files", "tiles"],
        help=(
            "Only query the filenames without downloading. "
            "Use value ``tiles`` to return tile indices instead of filenames."
        ),
    )
    parser.add_argument(
        "--tiling",
        type=str,
        metavar="FILENAME",
        help="Tiling Geojson file.",
    )
    parser.add_argument(
        "--data",
        type=str,
        metavar="PROVIDER",
        help="Data provider name: ``labs`` or ``None``",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="{workspace}/{tile}/{target}",
        help="""
        Output directory template where, for each target:

        * ``{workspace}`` is replaced with the workspace directory,
        * ``{tile}`` is replaced with the target tile index,
        * ``{target}`` is replaced with the input target object name or coordinates
          or ignored if the input target is a tile index.
        """,
    )

    parser.set_defaults(**parse_envargs("retrieve"), func=run)


def run(args):

    timer = Timer()

    logger.header(1, "Setup data provider")
    provider = DataProvider(vars(args)["from"], args.user, args.data, args.tiling)
    dsrs = args.dsr.split(",")
    modes = args.survey.split(",")
    # FIXME raise if len(dsrs/modes) == 0 => dedicated argparse type
    assert not args.force or len(args.targets) == 1
    ios = Workspace.from_args(args)
    timer.tic_log()

    logger.header(1, "Resolve targets")

    targets = []
    for t in args.targets:
        target = provider.query_target_tiles(dsrs, modes, args.radius, t)
        targets += target[: args.limit]
    timer.tic_log()

    if args.query_only == "tiles":
        write_pipe_args([t.tile for t in targets])
        return

    logger.header(1, "Retrieve targets", linebreaks=[1, 0])

    for progress, t in progress_str(targets):

        if args.force is not None and len(args.force) > 0:
            datafiles = args.force
        else:
            logger.header(2, f"{progress} Query datafiles for tile {t.tile}")
            datafiles = []
            for dsr in dsrs:
                logger.info(f"Dataset Release {dsr}")
                datafiles = provider.query_tile_datafiles(t.tile, dsr)
                if len(datafiles) > 0:
                    break  # TODO avoid breaks
            timer.tic_log()

        if args.force is None and len(datafiles) < 4:
            logger.error(f"Only {len(datafiles)} files found; Skip tile: {t.tile}")
            continue
        if args.force is None and len(datafiles) > 4:
            logger.warning(f"More than 4 files found: {len(datafiles)}.")

        if not args.query_only:
            workdir = io.make_workdir(t.workdir(ios))
            logger.header(2, f"{progress} Download and extract datafiles to: {workdir}")
            provider.download_datafiles(
                datafiles,
                workdir,  # FIXME give ios instead
                t,
                args.force is not None,
            )
            timer.tic_log()

    res = [ios.relative_to_workspace(t.workdir(ios)) for t in targets]
    write_pipe_args(res)
