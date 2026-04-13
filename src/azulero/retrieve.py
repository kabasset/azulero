# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.coordinates import SkyCoord

from azulero import io
from azulero.providers import dss, sas
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools.timing import Timer


providers = {
    "public": lambda: sas.SAS("PDR"),
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
        "--files",
        "-f",
        type=str,
        nargs="+",
        metavar="FILENAMES",
        help="Names of the files to be downloaded (bypasses query).",
    )
    parser.add_argument(
        "--query-only",
        "-q",
        action="store_true",
        help="Only query the filenames without downloading.",
    )

    parser.set_defaults(**parse_envargs("retrieve"), func=run)


def query_tiles(provider, dsrs: list[str], target: str):

    if target.isdigit():
        logger.info(f"Tile: {target}")
        return [(target, None)]

    if "," in target:
        logger.info(f"Coordinates: {target}")
        ra, dec = target.split(",")
        radec = SkyCoord(ra, dec, unit="deg")
    else:
        logger.info(f"Named object: {target}")
        radec = SkyCoord.from_name(target)
        logger.info(f"- Coordinates: {radec.ra.value:.2f}° {radec.dec.value:.2f}°")

    tiles = provider.query_tiles(radec, dsrs)
    for t in tiles:
        logger.info(f"- Tile: {t}")
    indices = set((t.index, target) for t in tiles)
    if len(indices) == 0:
        logger.warning("WARNING: No tile found!")
    return list(indices)


def query_datafiles(retriever, tile, dsr):

    logger.info(f"Query datafiles for tile {tile} and dataset release {dsr}:")

    datafiles = retriever.query_datafiles(tile, dsr)
    datafiles = {
        file: filter
        for file, filter in datafiles.items()
        if "VIS" in filter or "NIR" in filter
    }
    if len(datafiles) == 0:
        logger.warning("No datafile found.")

    for f in datafiles:
        logger.info(f"- [{datafiles[f]}] {f}")
    return datafiles


def download_datafiles(retriever, datafiles, workdir):

    logger.info(f"Download and extract datafiles to: {workdir}")

    for name in datafiles:  # TODO parallelize?
        path = workdir / name.removesuffix(".gz")
        if path.is_file():
            logger.warning(f"File exists; skip: {path.name}")
        else:
            retriever.download_datafile(name, path)
            logger.info(f"- {path}")


def run(args):

    timer = Timer()
    provider = providers[vars(args)["from"].lower()]()  # from is a Python keyword
    dsrs = args.dsr.split(",")
    assert args.files is None or len(args.tiles) == 1

    targets = []
    for t in args.targets:
        targets += query_tiles(provider, dsrs, t)

    for tile, _ in targets:
        if args.files is not None:
            datafiles = args.files
        else:
            for dsr in dsrs:
                datafiles = query_datafiles(provider, tile, dsr)
                if len(datafiles) > 0:
                    break
            timer.tic_log()
        if args.files is None and len(datafiles) < 4:
            logger.error(f"Only {len(datafiles)} files found; Skip tile: {tile}")
            continue
        if args.files is None and len(datafiles) > 4:
            logger.warning(f"More than 4 files found: {len(datafiles)}.")

        if not args.query_only:
            workdir = io.make_workdir(
                args.workspace, tile
            )  # FIXME download to targetdir
            download_datafiles(provider, datafiles, workdir)
            timer.tic_log()

    res = map(lambda t: t[0] if t[1] is None else "/".join(t), targets)
    if not write_pipe_args(res):
        res = " ".join(res)
        logger.command(f"azul --workspace {args.workspace} process {res}")
