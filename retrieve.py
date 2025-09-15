# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import argparse
import gzip
from pathlib import Path
import requests
import shutil
import subprocess


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


def get_products(tile, dsr):
    print(f"Query products for tile {tile}:")

    query = {
        "project": "EUCLID",
        "class_name": "DpdMerBksMosaic",
        "Data.TileIndex": tile,
        "Header.DataSetRelease": dsr,
        "fields": "Data.Filter.Name:Header.ProductId.LimitedString",
    }
    lines = requests.get(
        "https://eas-dps-rest-ops.esac.esa.int/REST", params=query
    ).text.split()
    products = [
        l.split(",")[-1].replace('"', "") for l in lines if ("VIS" in l or "NIR" in l)
    ]
    for p in products:
        print(f"- {p}")
    return products


def get_datafiles(products, output_dir):
    print(f"Download data files to: {output_dir}")
    for p in products:
        get_product_datafiles(p, output_dir)
        print(f"- {p}")


def get_product_datafiles(product, output_dir):
    cmd = [
        "E-Run",
        "ST_Operations",
        "ST_ArchiveClient",
        "--env",
        "ops",
        "--project",
        "EUCLID",
        "--with-files",
        "eas",
        "get",
        "--type",
        "DpdMerBksMosaic",
        "--id",
        f"'{product}'",
        "--files-include",
        "'EUC_MER_BGSUB*'",
        "--output",
        str(output_dir),
    ]
    subprocess.run(" ".join(cmd), shell=True, capture_output=True)
    # FIXME test result


def decompress(path):
    with gzip.open(path, "rb") as f_in:
        with open(path.with_suffix(""), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def decompress_datafiles(output_dir: Path):
    print(f"Decompress data files")
    for f in output_dir.iterdir():
        if f.suffix == ".gz":
            decompress(f)
            print(f"- {f}")


if __name__ == "__main__":
    args = parse_args()
    for tile in args.tiles:
        products = get_products(tile, args.dsr)
        if len(products) < 4:
            print(f"ERROR: Only {len(products)} products found; Skipping this tile.")
            continue
        if len(products) > 4:
            print(f"WARNING: More than 4 products found: {len(products)}.")
        output_dir = Path(args.output_dir).expanduser() / tile
        output_dir.mkdir(parents=True, exist_ok=True)
        get_datafiles(products, output_dir)
        decompress_datafiles(output_dir)
