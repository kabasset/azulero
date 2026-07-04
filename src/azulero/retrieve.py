# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from astropy.coordinates import Angle, SkyCoord

from azulero.image import io
from azulero.providers import dss, sas, tiling, cutout, datalabs
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools.timing import Timer
from azulero.tools.workspace import Workspace

tile_providers = {
    "pdr": lambda: sas.SAS("PDR"),
    "idr": lambda: sas.SAS("IDR"),
    "otf": lambda: sas.SAS("OTF"),
    "dss": lambda: dss.DSS(),  # TODO enable DSS selection
}

data_providers = {
    "labs": lambda provider: datalabs.Datalabs(provider),
}


def help_enumeration(values, coordination=", "):
    l = [str(v) for v in values]
    if len(l) == 1:
        return l[0]
    return ", ".join(list(l)[:-1]) + coordination + list(l)[-1]


def help_choice(values):
    return help_enumeration(values, " or ")


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
            "coordinates (e.g. 270.93°,67.05°), and/or object names (e.g. UGC11116)."
        ),
    )
    parser.add_argument(
        "--dsr",
        type=str,
        default="DR1_R2,DR1_R1,Q1_R1",
        metavar="LIST",
        help="Comma-separated list of data set releases in order of preference.",
    )
    parser.add_argument(
        "--from",
        type=str,
        default="idr",
        metavar="PROVIDER",
        help=f"Data provider: {help_choice(data_providers.keys())}.",
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
    parser.add_argument(
        "--tiling",
        type=str,
        default="DpdMerFinalCatalog.geojson",
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


def query_tiles(provider, dsrs: list[str], target: str):
    """
    Query the list of tiles for a given target, which may be a tile index, coordinates or object name.
    """

    if target.isdigit():
        logger.info(f"Tile: {target}")
        return [tiling.Target(target, target, None)]

    if "," in target:
        logger.info(f"Coordinates: {target}")
        ra, dec = target.split(",")
        radec = SkyCoord(ra, dec, unit="deg")
    else:
        logger.info(f"Named object: {target}")
        radec = SkyCoord.from_name(target)
        logger.bullet(f"Coordinates: {radec.ra.value:.2f}° {radec.dec.value:.2f}°")

    tiles = sorted(
        sorted(
            set(provider.query_tiles(radec, dsrs)),
            key=lambda t: t.distance,
        ),
        key=lambda t: t.mode,
    )

    for t in tiles:
        logger.bullet(f"Tile: {t}")
    targets = [tiling.Target(target, t.index, radec) for t in tiles]
    if len(targets) == 0:
        logger.warning("No tile found!")
    return list(targets)


def query_datafiles(provider, tile, dsr):

    logger.header(2, f"Query datafiles for tile {tile} and dataset release {dsr}:")

    datafiles = provider.query_datafiles(tile, dsr)
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


def download_datafiles(provider, datafiles, workdir, target, radius, overwrite):

    logger.header(2, f"Download and extract datafiles to: {workdir}")

    for name in datafiles:  # TODO parallelize?
        path = workdir / name.removesuffix(".gz")
        if path.is_file() and not overwrite:
            logger.bullet(f"File already exists; skip: {path.name}")
        else:
            logger.bullet(f"{path.name}")
            if path.is_file():
                logger.warning(f"Existing file will be overwritten: {path.name}")
            if radius is None:
                provider.download_datafile(name, path)
            else:
                provider.download_cutout(name, path, target, radius)


def run(args):

    timer = Timer()
    provider = tile_providers[vars(args)["from"].lower()]()  # from is a Python keyword
    tile_provider = (
        provider if hasattr(provider, "query_tiles") else tiling.Tiling(args.tiling)
    )
    if args.data is not None:
        data_provider = data_providers[args.data](provider)
    elif hasattr(provider, "donwload_cutout"):
        data_provider = provider
    else:
        data_provider = cutout.LocalCutout(provider)
    dsrs = args.dsr.split(",")
    assert not args.force or len(args.targets) == 1
    ios = Workspace.from_args(args)

    logger.header(1, "Resolve targets")

    targets = []
    for t in args.targets:
        targets += query_tiles(tile_provider, dsrs, t)[: args.limit]

    logger.header(1, "Retrieve targets", linebreaks=[1, 0])

    for t in targets:
        if args.force is not None and len(args.force) > 0:
            datafiles = args.force
        else:
            for dsr in dsrs:
                datafiles = query_datafiles(provider, t.tile, dsr)
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
            download_datafiles(
                data_provider,
                datafiles,
                workdir,  # FIXME give ios instead
                t,
                args.radius,
                args.force is not None,
            )
            timer.tic_log()

    res = [ios.relative_to_workspace(t.workdir(ios)) for t in targets]
    write_pipe_args(res)
