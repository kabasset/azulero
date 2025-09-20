# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import math
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
    parser.add_argument("--round", type=int, default=500, help="Image region rounding")

    parser.set_defaults(func=run)


def run(args):

    print()

    workdir = Path(args.workspace).expanduser() / args.tile

    timer = Timer()

    print(f"Read VIS channel: {workdir}")
    data = io.read_channel(workdir, "VIS")
    timer.tic_print()

    print(f"Prepare data.")
    h, w = data.shape
    data = np.clip(data[::10, ::10], 0, 1)
    im = plt.imshow(np.flipud(data), extent=[0, w, 0, h])
    timer.tic_print()

    plt.title("Zoom to select a region, then close the window.")
    plt.show()

    rounding = args.round
    x0, x1 = im.axes.get_xlim()
    y0, y1 = im.axes.get_ylim()
    x0 = math.floor(x0 / rounding) * rounding
    x1 = min(math.ceil(x1 / rounding) * rounding, w)
    y0 = math.floor(y0 / rounding) * rounding
    y1 = min(math.ceil(y1 / rounding) * rounding, h)

    print(f"\nYou may now run:")
    print(
        f"\nazul --workspace {args.workspace} process {args.tile}[{y0}:{y1},{x0}:{x1}]\n"
    )
