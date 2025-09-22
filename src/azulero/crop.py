# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import math
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from azulero import io
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "crop",
        help="Display the VIS channel for region selection.",
        description=(
            "Display the VIS channel between values 0 and 1 in a new window, "
            "and enable cropping a region by zooming in. "
            "When the window is closed, "
            "the program prints out the corresponding image processing command."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tile",
        type=str,
        metavar="INDEX",
        help="Tile index.",
    )
    parser.add_argument(
        "--round",
        type=int,
        default=500,
        metavar="INC",
        help=(
            "Image region rounding increment. "
            "The returned region is the smallest region which contains the selected region, "
            "and whose bounds are multiples of the increment."
        ),
    )

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
    im = plt.imshow(np.flipud(np.asinh(data / 0.7)), extent=[0, w, 0, h])
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
