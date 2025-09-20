# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse

from azulero import retrieve, process, crop


def run():

    parser = argparse.ArgumentParser(
        prog="azul", description="Bring colors to Euclid tiles!"
    )

    parser.add_argument("--workspace", type=str, default=".", help="Workspace")

    subparsers = parser.add_subparsers()
    retrieve.add_parser(subparsers)
    crop.add_parser(subparsers)
    process.add_parser(subparsers)

    args = parser.parse_args()
    args.func(args)
