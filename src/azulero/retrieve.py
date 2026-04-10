# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse

from azulero import io
from azulero.providers import astroq, dss, sas
from azulero.timing import Timer


providers = {"dss": dss.DSS, "sas": sas.SAS, "idr": astroq.AstroQuery}


def enumeration(values, coordination=", "):
    l = [str(v) for v in values]
    if len(l) == 1:
        return l[0]
    return ", ".join(list(l)[:-1]) + coordination + list(l)[-1]


def choice(values):
    return enumeration(values, " or ")


def add_parser(subparsers):

    parser = subparsers.add_parser(
        "retrieve",
        help="Retrieve MER datafiles.",
        description="Query and download datafiles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tiles",
        type=str,
        nargs="+",
        help="Space-separated list of tile indices.",
    )
    parser.add_argument(
        "--dsr",
        type=str,
        default="DR1_R2,DR1_R1,Q1_R1",
        metavar="LIST",
        help="Comma-separated list of data set releases.",
    )
    parser.add_argument(
        "--from",
        type=str,
        default="idr",
        metavar="PROVIDER",
        help=f"Data provider: {choice(providers.keys())}.",
    )
    parser.add_argument(
        "--files",
        "-f",
        type=str,
        nargs="+",
        metavar="FILENAMES",
        help="Names of the files to be downloaded (bypasses query).",
    )

    parser.set_defaults(func=run)


def query_datafiles(retriever, tile, dsr):

    print(f"Query datafiles for tile {tile} and dataset release {dsr}:")

    datafiles = retriever.query_datafiles(tile, dsr)
    datafiles = {
        file: filter
        for file, filter in datafiles.items()
        if "VIS" in filter or "NIR" in filter
    }
    if len(datafiles) == 0:
        print("- None found.")

    for f in datafiles:
        print(f"- [{datafiles[f]}] {f}")
    return datafiles


def download_datafiles(retriever, datafiles, workdir):

    print(f"Download and extract datafiles to: {workdir}")

    for name in datafiles:  # TODO parallelize?
        path = workdir / name.removesuffix(".gz")
        if path.is_file():
            print(f"WARNING: File exists; skip: {path.name}")
            continue
        retriever.download_datafile(name, path)
        print(f"- {path}")


def run(args):

    timer = Timer()
    provider = providers[vars(args)["from"]]()  # from is a Python keyword
    assert args.files is None or len(args.tiles) == 1
    for tile in args.tiles:  # TODO parallelize?
        workdir = io.make_workdir(args.workspace, tile)
        if args.files is not None:
            datafiles = args.files
        else:
            for dsr in args.dsr.split(","):
                datafiles = query_datafiles(provider, tile, dsr)
                if len(datafiles) > 0:
                    break
            timer.tic_print()
        if args.files is None and len(datafiles) < 4:
            print(f"ERROR: Only {len(datafiles)} files found; Skip tile: {tile}")
            continue
        if args.files is None and len(datafiles) > 4:
            print(f"WARNING: More than 4 files found: {len(datafiles)}.")
        download_datafiles(provider, datafiles, workdir)
        timer.tic_print()
        print(f"\nYou may now run:")
        print(f"\nazul --workspace {args.workspace} crop {tile}\n")
        print(f"or:")
        print(f"\nazul --workspace {args.workspace} process {tile}\n")
