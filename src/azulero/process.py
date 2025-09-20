# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path

from azulero import color, io, mask
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser("process", help="Process MER channels")

    parser.add_argument(
        "tile",
        type=str,
        help="Tile folder name and optional slicing",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.tiff",
        help="Output filename relative to the tile folder",
    )
    parser.add_argument(
        "--black",
        type=float,
        default=0.0,
        help="Black point (0 for background-subtracted inputs)",
    )
    parser.add_argument(
        "--white",
        type=float,
        default=10000.0,
        help="White point",
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=[500, 1.6, 1, 1],  # NIR passbands ~ 0.25, 0.4, 0.5, H = 1 boosts R
        help="Scaling factors for IYJH bands",
    )
    parser.add_argument("--nirl", type=float, default=0.5, help="NIR contribution to L")
    parser.add_argument("--yg", type=float, default=0.3, help="Y contribution to G")
    parser.add_argument("--ib", type=float, default=0.2, help="I contribution to B")
    parser.add_argument(
        "--stretch",
        type=float,
        default=0.7,
        help="Stretching parameter (arcsinh scaling factor)",
    )
    parser.add_argument(
        "--saturation", type=float, default=1.6, help="Saturation factor"
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
    io.write_tiff(res, workdir / "rgb.tiff")
    timer.tic_print()

    print(f"Inpaint invalid pixels")
    res = mask.inpaint(res, dead_nir)
    res = mask.inpaint(res, dead_vis)
    res[dead_vis] = mask.resaturate(res[dead_vis])
    res = mask.inpaint(res, hot)
    timer.tic_print()

    print(f"Write output to: {args.output}")
    io.write_tiff(res, workdir / args.output)
    timer.tic_print()
