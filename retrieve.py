# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import argparse
from pathlib import Path
import requests
import time


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "tiles",
        type=str,
        nargs="+",
        help="Tile indices",
    )
    parser.add_argument("--dsr", type=str, default="DR1_R1", help="Data set release")
    parser.add_argument(
        "--workspace", type=str, default="~/Downloads", help="Workspace"
    )

    return parser.parse_args()


class Timer(object):  # FIXME to lib

    def __init__(self):
        self.start = time.perf_counter()
        self.prev = self.start

    def tic(self):
        prev = self.prev
        self.prev = time.perf_counter()
        return self.prev - prev, self.prev - self.start

    def tic_print(self):
        split, total = self.tic()
        print(f"- Elapsed: {split}s [Total: {total}s]")


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
        r = requests.get(f"https://euclidsoc.esac.esa.int/{n}")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"- {path}")


def retrieve(args):
    timer = Timer()
    for tile in args.tiles:  # TODO parallelize?
        datafiles = query_datafiles(tile, args.dsr)
        timer.tic_print()
        if len(datafiles) < 4:
            print(f"ERROR: Only {len(datafiles)} files found; Skipping this tile.")
            continue
        if len(datafiles) > 4:
            print(f"WARNING: More than 4 files found: {len(datafiles)}.")
        workdir = make_workdir(args.workspace, tile)
        download_datafiles(datafiles, workdir)
        timer.tic_print()


if __name__ == "__main__":
    args = parse_args()
    retrieve(args)
