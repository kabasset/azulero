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
    Database wrapper which implements all services,
    possibly using surrogates approaches when the service is not natively supported.
    """

    def __init__(
        self,
        database: str,
        user: str | None = None,
        data_store: str | None = None,
        tiling_file: Path | None = None,
    ):
        self.product_db = product_databases[database](user)
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

    def query_tiles(
        self, dsrs: list[str], modes: list[str], radius: Angle, target: str
    ):
        """
        Query the list of tiles for a given target, which may be a tile index, coordinates or object name.
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

        @retry(logger=logger, default=[])
        def retry_query():
            return self.spatial_db.query_tiles(radec, dsrs)

        tiles = self.sort_tiles(retry_query(), dsrs, modes)

        for tile in tiles:
            logger.bullet(f"Tile: {tile}")
        targets = [tiling.Target(t, tile.index, radec, r) for tile in tiles]
        if len(targets) == 0:
            logger.warning("No tile found!")
        return list(targets)

    def sort_tiles(
        self, tiles: list[tiling.Tile], dsrs: list[str], modes: list[str]
    ) -> list[tiling.Tile]:
        res = set(t for t in tiles if (t.dsr in dsrs and t.mode in modes))
        res = sorted(res, key=lambda t: t.distance)
        res = sorted(res, key=lambda t: dsrs.index(t.dsr))
        res = sorted(res, key=lambda t: modes.index(t.mode))
        return res

    def query_datafiles(self, tile, dsr):

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

    def download_datafiles(self, datafiles, workdir, target, overwrite):

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
    provider = DataProvider(
        vars(args)["from"].lower(),
        args.user,
        args.data,
        args.tiling,
    )
    dsrs = args.dsr.split(",")  # FIXME raise if len(dsrs) = 0
    modes = args.survey.split(",")
    assert not args.force or len(args.targets) == 1
    ios = Workspace.from_args(args)
    timer.tic_log()

    logger.header(1, "Resolve targets")

    targets = []
    for t in args.targets:
        targets += provider.query_tiles(dsrs, modes, args.radius, t)[: args.limit]
    timer.tic_log()

    if args.query_only == "tiles":
        write_pipe_args([t.tile for t in targets])
        return

    logger.header(1, "Retrieve targets", linebreaks=[1, 0])

    for progress, t in progress_str(targets):
        datafiles = []
        if args.force is not None and len(args.force) > 0:
            datafiles = args.force
        else:
            for dsr in dsrs:
                logger.header(
                    2,
                    f"{progress} Query datafiles for tile {t.tile} and dataset release {dsr}:",
                )
                datafiles = provider.query_datafiles(t.tile, dsr)
                if len(datafiles) > 0:
                    break
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
