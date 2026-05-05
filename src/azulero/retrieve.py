# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from astropy.coordinates import Angle, SkyCoord

from azulero.image import io
from azulero.providers import dss, sas
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools.timing import Timer


providers = {
    "pdr": lambda: sas.SAS("PDR"),
    "idr": lambda: sas.SAS("IDR"),
    "otf": lambda: sas.SAS("OTF"),
    "dss": lambda: dss.DSS(),  # TODO enable DSS selection
}


def help_enumeration(values, coordination=", "):
    l = [str(v) for v in values]
    if len(l) == 1:
        return l[0]
    return ", ".join(list(l)[:-1]) + coordination + list(l)[-1]


def help_choice(values):
    return help_enumeration(values, " or ")


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "retrieve",
        help="Retrieve datafiles.",
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
            "coordinates (e.g. 270.93°,67.05°), and/or object names (e.g. UGC11116)."
        ),
    )
    parser.add_argument(
        "--dsr",
        type=str,
        default="DR1_R2,DR1_R1,Q1_R1",
        metavar="LIST",
        help="Comma-separated list of data set releases in order of preferrence.",
    )
    parser.add_argument(
        "--from",
        type=str,
        default="idr",
        metavar="PROVIDER",
        help=f"Data provider: {help_choice(providers.keys())}.",
    )
    parser.add_argument(
        "--radius",
        "-r",
        type=Angle,
        default=None,
        metavar="ANGLE",
        help="Cone search angle (if set, will retrieve cutouts instead of tiles).",
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
        action="store_true",
        help="Only query the filenames without downloading.",
    )

    parser.set_defaults(**parse_envargs("retrieve"), func=run)


@dataclass(frozen=True)
class Target:

    name: str
    index: str
    coord: SkyCoord | None = field(default=None, compare=False)

    def workdir(self):
        if self.name == self.index:
            return self.index
        return str(Path(self.index) / self.name)


def query_tiles(provider, dsrs: list[str], target: str):
    """
    Query the list of tiles for a given target, which may be a tile index, coordinates or object name.
    """

    if target.isdigit():
        logger.info(f"Tile: {target}")
        return [Target(target, target, None)]

    if "," in target:
        logger.info(f"Coordinates: {target}")
        ra, dec = target.split(",")
        radec = SkyCoord(ra, dec, unit="deg")
    else:
        logger.info(f"Named object: {target}")
        radec = SkyCoord.from_name(target)
        logger.bullet(f"Coordinates: {radec.ra.value:.2f}° {radec.dec.value:.2f}°")

    tiles = provider.query_tiles(radec, dsrs)
    for t in tiles:
        logger.bullet(f"Tile: {t}")
    targets = [Target(target, t.index, radec) for t in tiles]
    if len(targets) == 0:
        logger.warning("No tile found!")
    return list(targets)


def query_datafiles(retriever, tile, dsr):

    logger.header(2, f"Query datafiles for tile {tile} and dataset release {dsr}:")

    datafiles = retriever.query_datafiles(tile, dsr)
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


def download_datafiles(retriever, datafiles, workdir, target, radius, overwrite):

    logger.header(2, f"Download and extract datafiles to: {workdir}")

    for name in datafiles:  # TODO parallelize?
        path = workdir / name.removesuffix(".gz")
        if path.is_file() and not overwrite:
            logger.bullet(f"File already exists; skip: {path.name}")
        else:
            if path.is_file():
                logger.warning(f"Existing file will be overwritten: {path.name}")
            args = [] if radius is None else [target, radius]
            retriever.download_datafile(name, path, *args)
            logger.bullet(f"{path}")


def run(args):

    timer = Timer()
    provider = providers[vars(args)["from"].lower()]()  # from is a Python keyword
    dsrs = args.dsr.split(",")
    assert not args.force or len(args.targets) == 1

    logger.header(1, "Resolve targets")

    targets = []
    for t in args.targets:
        targets += query_tiles(provider, dsrs, t)[: args.limit]

    logger.header(1, "Retrieve targets", linebreaks=[1, 0])

    for t in targets:
        if args.force is not None and len(args.force) > 0:
            datafiles = args.force
        else:
            for dsr in dsrs:
                datafiles = query_datafiles(provider, t.index, dsr)
                if len(datafiles) > 0:
                    break
            timer.tic_log()
        if args.force is None and len(datafiles) < 4:
            logger.error(f"Only {len(datafiles)} files found; Skip tile: {t.index}")
            continue
        if args.force is None and len(datafiles) > 4:
            logger.warning(f"More than 4 files found: {len(datafiles)}.")

        if not args.query_only:
            workdir = io.make_workdir(args.workspace, t.workdir())
            download_datafiles(
                provider, datafiles, workdir, t, args.radius, args.force is not None
            )
            timer.tic_log()

    res = [t.workdir() for t in targets]
    if not write_pipe_args(res):
        res = " ".join(res)
        logger.command(f"azul --workspace {args.workspace} process {res}")
