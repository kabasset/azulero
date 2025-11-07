# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse

from azulero import assemble, retrieve, crop, tune, process, roam


def run():

    parser = argparse.ArgumentParser(
        prog="azul",
        description="Bring colors to Euclid tiles!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--workspace", type=str, default=".", metavar="PATH", help="Parent workspace"
    )

    subparsers = parser.add_subparsers(title="Commands")
    retrieve.add_parser(subparsers)
    crop.add_parser(subparsers)
    tune.add_parser(subparsers)
    process.add_parser(subparsers)
    assemble.add_parser(subparsers)
    roam.add_parser(subparsers)

    args = parser.parse_args()
    args.func(args)
