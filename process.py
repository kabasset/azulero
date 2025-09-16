# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import argparse
import time
import numpy as np
from pathlib import Path

from azul import color, io, mask


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "tile",
        type=str,
        help="Tile folder name",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.tiff",
        help="Output filename relative to the tile folder",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="~/Downloads",
        help="Working directory, containing the tile folder",
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
        help="White point (-1 to use the max intensity)",
    )
    parser.add_argument(
        "--slice",
        type=str,
        default=None,
        help="Input images region following Python slicing syntax",
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=[0.00234, 0.65, 1.00, 1.14],
        help="Inverse scaling factors for IYJH bands",
    )
    parser.add_argument(
        "--yb", type=float, default=0.7, help="Y to B transmission factor"
    )
    parser.add_argument(
        "--hl", type=float, default=0.3, help="H to L transmission factor"
    )
    parser.add_argument(
        "--stretch",
        type=float,
        default=0.7,
        help="Stretching parameter (inverse arcsinh scaling factor)",
    )
    parser.add_argument(
        "--saturation", type=float, default=1.6, help="Saturation factor"
    )
    return parser.parse_args()


class Timer(object):

    def __init__(self):
        self.start = time.perf_counter()
        self.prev = self.start

    def tic(self):
        prev = self.prev
        self.prev = time.perf_counter()
        return self.prev - prev, self.prev - self.start

    def tic_print(self):
        split, total = self.tic()
        print(f"- Elapsed: {split}s [Total: {total}s]")


def process(args):
    transform = color.Transform(
        iyjh_scaling=list(args.scaling),
        y_to_b=args.yb,
        h_to_l=args.hl,
        saturation=args.saturation,
        stretch=args.stretch,
        span=(args.black, args.white),
    )

    workdir = Path(args.workspace).expanduser() / args.tile

    timer = Timer()

    print(f"Read IYJH image from: {workdir}")
    iyjh = io.read_iyjh(workdir, io.parse_slice(args.slice))
    print(f"- Size: {iyjh.shape[2]} x {iyjh.shape[1]} x {iyjh.shape[0]}")
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


if __name__ == "__main__":
    args = parse_args()
    process(args)
