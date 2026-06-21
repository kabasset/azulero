# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse

from azulero import (
    retrieve,
    process,
    arrange,
    overlay,
    roam,
    crop,
    find,
    assemble,
)
from azulero.tools.messaging import logger, parse_envargs, write_pipe_args

from azulero import _version


def add_parser():

    parser = argparse.ArgumentParser(
        prog="azul [global_options]",
        usage="%(prog)s <cmd> [options]",
        description=_version.__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--workspace", type=str, default=".", metavar="PATH", help="Parent workspace"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="*[-_]{channel}[-_]*.fits",
        metavar="PATTERN",
        help="Input file pattern, where ``{channel}`` is replaced with the channel name",
    )
    parser.add_argument(
        "--channels",
        type=str,
        nargs=4,
        metavar=("I_NAME", "Y_NAME", "J_NAME", "H_NAME"),
        default=["VIS", "NIR-Y", "NIR-J", "NIR-H"],
        help="Channel names to be rendered in the input file pattern.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="INFO",
        metavar="LEVEL",
        help=f"Log level.",
    )

    subparsers = parser.add_subparsers(title="Commands", dest="cmd")
    retrieve.add_parser(subparsers, "Retrieve channels of MER tiles or cutouts.")
    process.add_parser(subparsers, "Process MER channels to render a color image.")
    arrange.add_parser(subparsers, "Arrange images into a grid.")
    roam.add_parser(subparsers, "Create videos which roam through images.")
    subparsers.add_parser("cite", help="Print citation instructions.")

    find.add_parser(subparsers, "DEPRECATED")
    crop.add_parser(subparsers, "DEPRECATED")
    assemble.add_parser(subparsers, "DEPRECATED")
    overlay.add_parser(subparsers, "DEPRECATED")

    # TODO read .env first
    parser.set_defaults(**parse_envargs())

    return parser


def run():
    parser = add_parser()
    args = parser.parse_args()

    logger.setLevel(args.log)

    log_title()

    if args.cmd != "cite":
        log_args(args)
        args.func(args)

    if args.cmd == "cite":
        citation = log_citation()
        write_pipe_args(citation, log=False)

    logger.info("")


def log_title():
    logger.header(1, f"  Azulero v{_version.__version__}", linebreaks=[1, 0])
    logger.header(2, f"  Antoine Basset, CNES", linebreaks=[0])
    logger.header(3, f"  {_version.__url__}", linebreaks=[0, 1])


def log_args(args):
    logger.info(f"Command: {args.cmd}")
    for k in vars(args):
        if k not in ["func", "cmd"]:
            logger.info(f"  {k}: {vars(args)[k]}")


def log_citation():
    logger.header(1, "Citation", linebreaks=[0, 0])

    logger.header(
        2, "If you publish images rendered with this software, please credit:"
    )
    logger.info(
        f"Image processing with Azulero v{_version.__version__} (Antoine Basset, CNES)"
    )

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
        "doi": _version.__url__.split("doi.org/")[-1],
    }
    lines = bibtex_citation("software", "Basset_Azulero", citation)
    for l in lines:
        logger.info(l)
    return lines


def bibtex_citation(type, name, fields):
    enumeration = lambda e: " and ".join(e)
    line = lambda n, v: (
        n + " = {" + (enumeration(v) if isinstance(v, list) else v) + "}"
    )
    lines = ",\n".join(f"  {line(f, fields[f])}" for f in fields).split("\n")
    return ["@" + type + "{" + name + ","] + lines + ["}"]


if __name__ == "__main__":
    run()
