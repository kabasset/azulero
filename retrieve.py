# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import argparse
import gzip
from pathlib import Path
import requests
import shutil
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
        "--output-dir", type=str, default="~/Downloads", help="Output parent directory"
    )

    return parser.parse_args()


class Timer(object): # FIXME to lib

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
    lines = requests.get(
        "https://eas-dps-rest-ops.esac.esa.int/REST", params=query
    ).text.replace('"', "").split()
    datafiles = {}
    for l in lines:
        if "VIS" in l or "NIR" in l:
            file_name, filter_name = l.split(",")
            datafiles[file_name] = filter_name
    for f in datafiles:
        print(f"- [{datafiles[f]}] {f}")
    return datafiles


def download_datafiles(datafiles, output_dir):
    print(f"Download datafiles to: {output_dir}")

    for n in datafiles: # TODO parallelize?
        url = f"https://euclidsoc.esac.esa.int/{n}"
        print(f"- URL: {url}")
        path = (output_dir / n).with_suffix("")
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"- Downloaded: {path}")


def decompress(path):
    print(path)
    res = path.with_suffix("")
    print(res)
    with gzip.open(path, "rb") as f_in:
        with open(res, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return res


if __name__ == "__main__":
    args = parse_args()
    timer = Timer()
    for tile in args.tiles: # TODO parallelize?
        datafiles = query_datafiles(tile, args.dsr)
        timer.tic_print()
        if len(datafiles) < 4:
            print(f"ERROR: Only {len(datafiles)} files found; Skipping this tile.")
            continue
        if len(datafiles) > 4:
            print(f"WARNING: More than 4 files found: {len(datafiles)}.")
        output_dir = Path(args.output_dir).expanduser() / tile
        output_dir.mkdir(parents=True, exist_ok=True)
        download_datafiles(datafiles, output_dir)
        timer.tic_print()
