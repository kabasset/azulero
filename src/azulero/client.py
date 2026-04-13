# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from importlib import metadata

from azulero import assemble, find, overlay, retrieve, crop, tune, process, roam
from azulero.tools.messaging import logger, colorize, parse_envargs


def run():

    parser = argparse.ArgumentParser(
        prog="azul",
        description="Bring colors to Euclid tiles!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--workspace", type=str, default=".", metavar="PATH", help="Parent workspace"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="*[-_]{channel}[-_]*.fits",
        metavar="PATTERN",
        help="Input file pattern, where `{channel}` is replaced with the channel name, e.g. `NIR-Y`",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="INFO",
        metavar="LEVEL",
        help=f"Log level.",
    )

    subparsers = parser.add_subparsers(title="Commands", dest="cmd")
    find.add_parser(subparsers)
    retrieve.add_parser(subparsers)
    crop.add_parser(subparsers)
    tune.add_parser(subparsers)
    process.add_parser(subparsers)
    assemble.add_parser(subparsers)
    roam.add_parser(subparsers)
    overlay.add_parser(subparsers)

    parser.set_defaults(**parse_envargs())
    args = parser.parse_args()

    logger.setLevel(args.log)
    logger.info("")
    logger.header(f"  Azulero v{metadata.version('azulero')}", 1)
    logger.header(f"  Antoine Basset, CNES", 2)
    logger.header(f"  http://doi.org/10.24400/815952/Azulero", 3)
    logger.info("")

    logger.info(f"Command: {args.cmd}")
    for k in vars(args):
        if k not in ["func", "cmd"]:
            logger.info(f"  {k}: {vars(args)[k]}")
    logger.info("")

    args.func(args)


if __name__ == "__main__":
    run()
