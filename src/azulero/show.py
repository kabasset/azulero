# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from azulero import color, io, mask
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "show", help="Show VIS channel between values 0 and 1"
    )

    parser.add_argument(
        "tile",
        type=str,
        help="Tile folder name",
    )

    parser.set_defaults(func=run)


def run(args):

    workdir = Path(args.workspace).expanduser() / args.tile

    timer = Timer()

    print(f"Read VIS channel: {workdir}")
    data = io.read_channel(workdir, "VIS")
    timer.tic_print()

    print(f"Prepare data.")
    h, w = data.shape
    data = np.clip(data[::10, ::10], 0, 1)
    plt.imshow(data, extent=[0, w, 0, h])
    timer.tic_print()

    plt.show()
