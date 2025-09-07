# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

import argparse
from pathlib import Path

from azul import color, io


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "workdir",
        type=str,
        help="Working directory, containing input images",
    )
    parser.add_argument(
        "output",
        type=str,
        help="Output filename relative to the working directory",
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
        "--yb", type=float, default=0.6, help="Y to B transmission factor"
    )
    parser.add_argument(
        "--hl", type=float, default=0.3, help="H to L transmission factor"
    )
    parser.add_argument(
        "--saturation", type=float, default=1.0, help="Saturation level"
    )
    return parser.parse_args()


def process(args):
    print(f"Read IYJH images in: {args.workdir}")
    tile = io.read_iyjh(Path(args.workdir), args.slice)
    transform = color.Transform(
        iyjh_scaling=list(args.scaling),
        y_to_b=args.yb,
        h_to_l=args.hl,
        saturation=args.saturation,
    )
    print(f"Transform IYJH to RGB image")
    res = color.iyjh_to_rgb(tile, transform)
    print(f"Write output to: {args.output}")
    io.write_tiff(res, Path(args.workdir) / args.output)
    print(f"Done.")


if __name__ == "__main__":
    args = parse_args()
    process(args)
