# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import math
import numpy as np
from pathlib import Path

from azulero.image import io, roi
from azulero.tools.messaging import write_pipe_args
from azulero.tools.timing import Timer


def add_parser(subparsers, help):
    parser = subparsers.add_parser(
        "crop",
        help=help,
        description=(
            "Display the first channel in a workdir and select a region in a GUI."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "workdir",
        type=str,
        metavar="PATH",
        help="Workdir relative to the workspace.",
    )
    parser.add_argument(
        "--white", "-w", type=float, default=1.0, metavar="VALUE", help="White point"
    )
    parser.add_argument(
        "--downsample",
        type=int,
        default=10,
        metavar="STEP",
        help="Integral downsampling factor for performance",
    )
    parser.add_argument(
        "--round",
        type=int,
        default=600,
        metavar="PIXELS",
        help=(
            "Image region rounding increment. "
            "The returned region is the smallest region which contains the selected region, "
            "and whose bounds are multiples of the increment."
        ),
    )

    parser.set_defaults(func=run)


def run(args):

    workdir = Path(args.workspace).expanduser() / args.workdir

    timer = Timer()

    print(f"Read {args.channels[0]} channel in: {workdir}")
    data = io.read_channel(workdir, args.input.format(channel=args.channels[0]))
    shape = data.shape
    data = np.asinh(
        np.clip(data[:: args.downsample, :: args.downsample], 0, args.white) / 0.7
    )
    data = np.stack([data, data, data], axis=-1)
    timer.tic_log()

    print(f"Run GUI.")
    select = roi.RectSelector(data)
    slicing = select()
    timer.tic_log()

    rounding = args.round
    x0 = slicing[1].start * args.downsample
    x0 = math.floor(x0 / rounding) * rounding
    x1 = slicing[1].stop * args.downsample
    x1 = min(math.ceil(x1 / rounding) * rounding, shape[1])
    y0 = slicing[0].start * args.downsample
    y0 = math.floor(y0 / rounding) * rounding
    y1 = slicing[0].stop * args.downsample
    y1 = min(math.ceil(y1 / rounding) * rounding, shape[0])

    write_pipe_args([f"{args.workdir}[{y0}:{y1},{x0}:{x1}]"])
