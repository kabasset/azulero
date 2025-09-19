# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.io import fits
import csv


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tiling",
        type=str,
        help="Tile catalog with list of noteworthy objects",
    )
    parser.add_argument("output", type=str, help="Output objects catalog")
    return parser.parse_args()


def process(tiling):

    print(f"Reading tile catalog: {tiling}")
    hdul = fits.open(tiling)
    data = hdul[1].data
    tiles = data["tileId"]
    objects = data["comment"]
    print(f"- Tiles: {len(tiles)}")
    res = {int(t): "".join(o).split(",") for t, o in zip(tiles, objects) if len(o) > 1}
    print(f"- Objects: {len(res)}")
    return res


def write(catalog, output):
    print(f"Writing object catalog: {output}")
    with open(output, "w") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Tile", "Count", "Objects"])
        for t in catalog:
            objects = catalog[t]
            w.writerow([str(t), len(objects), ", ".join(objects)])


if __name__ == "__main__":

    args = parse_args()
    catalog = process(args.tiling)
    write(catalog, args.output)
