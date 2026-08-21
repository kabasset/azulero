# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.coordinates import Angle

from azulero.image import io
from azulero.providers import factory
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
    progress_str,
)
from azulero.tools.timing import Timer
from azulero.tools.workspace import Workspace


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
        choices=factory.product_databases.keys(),
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
          or ignored if the input target is a tile index,
        * ``{dsr}`` is replaced with the dataset release name,
        * ``{radius}`` is replaced with the cutout radius
          or ignored if the target is a complete tile.
        """,
    )

    parser.set_defaults(**parse_envargs("retrieve"), func=run)


def run(args):

    timer = Timer()

    logger.header(1, "Setup data provider")
    provider = factory.DataProvider(
        vars(args)["from"],
        args.user,
        args.data,
        args.tiling,
    )
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
        write_pipe_args([t.tile.index for t in targets])
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
                datafiles = provider.query_tile_datafiles(t.tile)
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
