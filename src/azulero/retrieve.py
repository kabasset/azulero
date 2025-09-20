# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from pathlib import Path
import requests

from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser("retrieve", help="Retrieve MER datafiles")

    parser.add_argument(
        "tiles",
        type=str,
        nargs="+",
        help="Tile indices",
    )
    parser.add_argument("--dsr", type=str, default="DR1_R1", help="Data set release")

    parser.set_defaults(func=run)


def query_datafiles(tile, dsr):
    print(f"Query datafiles for tile {tile}:")

    query = {
        "project": "EUCLID",
        "class_name": "DpdMerBksMosaic",
        "Data.TileIndex": tile,
        "Header.DataSetRelease": dsr,
        "fields": "Data.DataStorage.DataContainer.FileName:Data.Filter.Name",
    }
    lines = (
        requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        .text.replace('"', "")
        .split()
    )
    datafiles = {}
    for l in lines:
        if "VIS" in l or "NIR" in l:
            file_name, filter_name = l.split(",")
            datafiles[file_name] = filter_name
    for f in datafiles:
        print(f"- [{datafiles[f]}] {f}")
    return datafiles


def make_workdir(workspace, tile):
    workdir = Path(workspace).expanduser() / tile
    if workdir.is_dir():
        print("WARNING: Working directory already exists.")
    else:
        workdir.mkdir(parents=True)
    return workdir


def download_datafiles(datafiles, workdir):
    print(f"Download and extract datafiles to: {workdir}")

    for n in datafiles:  # TODO parallelize?
        path = (workdir / n).with_suffix("")
        if path.is_file():
            print(f"WARNING: File existd; skip: {path.name}")
            continue
        r = requests.get(f"https://euclidsoc.esac.esa.int/{n}")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"- {path}")


def run(args):

    print()

    timer = Timer()
    for tile in args.tiles:  # TODO parallelize?
        workdir = make_workdir(args.workspace, tile)
        datafiles = query_datafiles(tile, args.dsr)
        timer.tic_print()
        if len(datafiles) < 4:
            print(f"ERROR: Only {len(datafiles)} files found; Skipping this tile.")
            continue
        if len(datafiles) > 4:
            print(f"WARNING: More than 4 files found: {len(datafiles)}.")
        download_datafiles(datafiles, workdir)
        timer.tic_print()
        print(f"\nYou may now run:")
        print(f"\nazul --workspace {args.workspace} show {tile}\n")
        print(f"or:")
        print(f"\nazul --workspace {args.workspace} process {tile}\n")
