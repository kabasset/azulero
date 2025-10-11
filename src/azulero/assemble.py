# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import yaml

from azulero import color, io, mask
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "assemble",
        help="Assemble tile patches for testing purposes.",
        description=(
            "Assemble tile patches in a grid, "
            "in order to process a varied collection of objects and tune parameters."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tiles",
        type=str,
        metavar="SPECS",
        help="Path to the YAML configuration file (list of tile specs), relative to the workspace",
    )
    # parser.add_argument( # FIXME
    #     "--cols", "-c", metaval="COUNT", help="Maximum number of columns"
    # )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="ASSEMBLAGE",
        metavar="PATH",
        help="Output assemblage directory.",
    )

    parser.set_defaults(func=run)


def run(args):

    print()

    timer = Timer()
    workspace = Path(args.workspace).expanduser()

    print("Read patches")
    patches = []
    with open(workspace / args.tiles, "r") as f:
        tiles = yaml.safe_load(f)
    for tile in tiles:
        print(f"- {tile}")
        tile, slicing = io.parse_tile(tile)
        workdir = workspace / tile
        patch = io.read_iyjh(workdir, slicing)
        print(f"- Shape: {patch.shape[1]} x {patch.shape[2]}")
        patches.append(patch)
        timer.tic_print()

    print("Assemble")
    assemblage = np.concatenate(patches, axis=2)
    print(f"- Shape: {assemblage.shape[1]} x {assemblage.shape[2]}")
    timer.tic_print()

    print("Write channels")
    workdir = io.make_workdir(workspace, args.output_dir)
    for name, channel in zip(("VIS", "NIR-Y", "NIR-J", "NIR-H"), assemblage):
        path = workdir / f"EUC_{name}_ASSEMBLAGE.fits"
        print(f"- [{name}] {path}")
        io.write_fits(channel, path)
    timer.tic_print()
