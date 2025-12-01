# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import gzip
from io import BytesIO
import requests

from azulero import io
from azulero.timing import Timer


class DSS(object):

    def query_datafiles(self, tile, dsr):

        query = {
            "project": "EUCLID",
            "class_name": "DpdMerBksMosaic",
            "Data.TileIndex": tile,
            "Header.DataSetRelease": dsr,
            "fields": "Data.DataStorage.DataContainer.FileName:Data.Filter.Name",
        }

        r = requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        r.raise_for_status()

        lines = r.text.replace('"', "").split()
        datafiles = {}
        for l in lines:
            if "VIS" in l or "NIR" in l:
                file_name, filter_name = l.split(",")
                datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name, path):

        r = requests.get(f"https://euclidsoc.esac.esa.int/{name}")
        r.raise_for_status()

        # FIXME download and decompress in free function?
        with gzip.GzipFile(fileobj=BytesIO(r.content)) as f:
            content = f.read()
        with open(path, "wb") as f:
            f.write(content)


class SAS(object):

    def query_datafiles(self, tile, dsr):
        adql = (
            f"SELECT TOP 50 file_name, filter_name FROM sedm.mosaic_product"
            f" WHERE (release_name='{dsr}')"
            f" AND (category='SCIENCE')"
            f" AND (tile_index={tile})"
            f" AND (instrument_name IN ('VIS', 'NISP'))"
        )
        query = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "csv",
            "QUERY": adql.replace(" ", "+"),
        }
        url = "https://eas.esac.esa.int/tap-server/tap/sync?" + "&".join(
            f"{p}={query[p]}" for p in query
        )
        r = requests.get(url)  # Cannot use params as adql characters would be escaped
        r.raise_for_status()

        lines = r.text.split()
        datafiles = {}
        for l in lines[1:]:
            file_name, filter_name = l.split(",")
            datafiles[file_name] = filter_name
        return datafiles

    def download_datafile(self, name, path):

        query = {"file_name": name, "release": "sedm", "RETRIEVAL_TYPE": "FILE"}
        r = requests.get(f"https://eas.esac.esa.int/sas-dd/data", query)
        r.raise_for_status()

        with open(path, "wb") as f:
            f.write(r.content)


providers = {"dss": DSS, "sas": SAS}


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
        metavar="INDICES",
        help="Space-separated list of tile indices.",
    )
    parser.add_argument(
        "--dsr",
        type=str,
        default="DR1_R2,DR1_R1,Q1_R1",
        help="Comma-separated list of data set releases.",
    )
    parser.add_argument(
        "--from",
        type=str,
        default="dss",
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

    print()

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
