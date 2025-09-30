# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path

from azulero import color, io, mask
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "process",
        help="Process MER channels.",
        description=(
            "Process MER channels: "
            "1. Scale each channel; "
            "2. Blend IYJH channels into RGB and lightness (L) channels; "
            "3. Stretch dynamic range using arcsinh function; "
            "4. Set black and white points; "
            "5. Boost color saturation; "
            "6. Inpaint bad pixels."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tile",
        type=str,
        metavar="SPEC",
        help="Tile index and optional slicing à-la NumPy, e.g. 102160611[1500:7500,11500:17500]",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="{tile}_{step}.tiff",
        metavar="TEMPLATE",
        help=(
            "Output filename or template, relative to the tile folder. "
            "Placeholder {tile} is replaced by the tile index, "
            "and {step} is replaced by the processing step. "
            "If {step} is not present in the template, "
            "intermediate steps are not saved."
        ),
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=[500, 1.6, 1, 1],  # NIR passbands ~ 0.25, 0.4, 0.5, H = 1 boosts R
        metavar=("GAIN_I", "GAIN_Y", "GAIN_J", "GAIN_H"),
        help="Scaling factors applied immediately to the IYJH bands",
    )
    parser.add_argument(
        "--nirl",
        type=float,
        default=0.5,
        metavar="RATE",
        help="NIR contribution to L, between 0 and 1.",
    )
    parser.add_argument(
        "--ib",
        type=float,
        default=0.2,
        metavar="RATE",
        help="I contribution to B, between 0 and 1.",
    )
    parser.add_argument(
        "--yg",
        type=float,
        default=0.3,
        metavar="RATE",
        help="Y contribution to G, between 0 and 1.",
    )
    parser.add_argument(
        "--stretch",
        "-a",
        type=float,
        default=0.7,
        metavar="FACTOR",
        help="Scaling factor `a` in `arcsinh(data * a)`.",
    )
    parser.add_argument(
        "--black",
        "-b",
        type=float,
        default=0.0,
        metavar="VALUE",
        help="Black point, which may be 0 for background-subtracted inputs.",
    )
    parser.add_argument(
        "--white",
        "-w",
        type=float,
        default=1000.0,
        metavar="VALUE",
        help="White point.",
    )
    parser.add_argument(
        "--saturation",
        type=float,
        default=1.6,
        metavar="GAIN",
        help="Saturation factor",
    )

    parser.set_defaults(func=run)


def run(args):

    print()

    transform = color.Transform(
        iyjh_scaling=np.array(args.scaling),
        nir_to_l=args.nirl,
        y_to_g=args.yg,
        i_to_b=args.ib,
        saturation=args.saturation,
        stretch=args.stretch,
        bw=np.array([args.black, args.white]),
    )

    tile, slicing = io.parse_tile(args.tile)
    workdir = Path(args.workspace).expanduser() / tile
    name = args.output.replace("{tile}", tile)

    timer = Timer()

    print(f"Read IYJH image from: {workdir}")
    iyjh = io.read_iyjh(workdir, slicing)
    print(f"- Shape: {iyjh.shape[1]} x {iyjh.shape[2]}")
    timer.tic_print()

    print(f"Detect invalid pixels")
    dead_vis, dead_nir = mask.dead_pixels(*iyjh)
    hot = mask.hot_pixels(*iyjh)
    print(f"- Dead VIS: {np.sum(dead_vis)}")
    print(f"- Dead NIR: {np.sum(dead_nir)}")
    print(f"- Hot: {np.sum(hot)}")
    timer.tic_print()

    print(f"Transform IYJH to RGB image")
    res = color.iyjh_to_rgb(iyjh, transform)
    del iyjh
    if "{step}" in name:
        path = workdir / name.replace("{step}", "blended")
        print(f"- Write intermediate output: {path.name}")
        io.write_tiff(res, path)
    timer.tic_print()

    print(f"Inpaint invalid pixels")
    res = mask.inpaint(res, dead_nir)
    res = mask.inpaint(res, dead_vis)
    res[dead_vis] = mask.resaturate(res[dead_vis])
    res = mask.inpaint(res, hot)
    timer.tic_print()

    path = workdir / name.replace("{step}", "inpainted")
    print(f"Write output: {path.name}")
    io.write_tiff(res, path)
    timer.tic_print()
