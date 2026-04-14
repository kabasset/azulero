# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse

from azulero import assemble, find, overlay, retrieve, crop, tune, process, roam
from azulero.tools.messaging import logger, parse_envargs

from azulero import _version


def run():

    parser = argparse.ArgumentParser(
        prog="azul",
        description=_version.__description__,
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
    logger.header(1, f"  Azulero v{_version.__version__}", linebreaks=[1, 0])
    logger.header(2, f"  Antoine Basset, CNES", linebreaks=[0])
    logger.header(3, f"  http://doi.org/10.24400/815952/Azulero", linebreaks=[0, 1])

    logger.info(f"Command: {args.cmd}")
    for k in vars(args):
        if k not in ["func", "cmd"]:
            logger.info(f"  {k}: {vars(args)[k]}")

    args.func(args)

    logger.header(1, "Acknowledgement", linebreaks=[1, 0])

    logger.header(
        2, "If you publish images rendered with this software, please credit:"
    )
    logger.info(f"Image processing with Azulero v{_version.__version__} (CNES)")

    logger.header(
        2, "If you use this software for academic publications, please cite as follows:"
    )
    capitalize = lambda text: text[0].upper() + text[1:]
    citation = {
        "author": _version.__author__,
        "license": _version.__license__,
        "title": capitalize(_version.__name_soft__),
        "version": _version.__version__,
        "year": "2026",
        "url": _version.__url__,
        "doi": _version.__url__.split("doi.org/")[-1],
    }
    log_citation("software", "Basset_Azulero", citation)

    logger.info("")


def log_citation(type, name, fields):
    enumeration = lambda e: " and ".join(e)
    line = lambda n, v: (
        n + " = {" + (enumeration(v) if isinstance(v, list) else v) + "}"
    )
    logger.info("@" + type + "{" + name + ",")
    lines = ",\n".join(f"  {line(f, fields[f])}" for f in fields).split("\n")
    for l in lines:
        logger.info(l)
    logger.info("}")


if __name__ == "__main__":
    run()
