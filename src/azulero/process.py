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
        help="Process MER channels to render a color image.",
        description=(
            "Process MER channels: "
            "1. Inpaint dead pixels; "
            "2. Sharpen IYJH channels; "
            "3. Stretch dynamic range with asinh function; "
            "4. Blend IYJH channels into RGB and lightness (L) channels; "
            "5. Shift hue and boost color saturation; "
            "6. Adjust curves."
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
        "--zero",
        nargs=4,
        type=float,
        default=[24.5, 29.8, 30.1, 30.0],
        metavar=("ZP_I", "ZP_Y", "ZP_J", "ZP_H"),
        help="Zero points for each band",
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=[2.2, 1.3, 1.2, 1.0],
        metavar=("GAIN_I", "GAIN_Y", "GAIN_J", "GAIN_H"),
        help="Scaling factors applied immediately to the IYJH bands for white balance",
    )
    parser.add_argument(
        "--fwhm",
        nargs=4,
        type=float,
        default=[1.6, 3.5, 3.4, 3.5],
        metavar=("FWHM_I", "FWHM_Y", "FWHM_J", "FWHM_H"),
        help="FWHM for each band",
    )
    parser.add_argument(
        "--sharpen",
        type=float,
        default=0.5,
        metavar="STRENGTH",
        help="Strength of the sharpening",
    )
    parser.add_argument(
        "--nirl",
        type=float,
        default=0.1,
        metavar="RATE",
        help="NIR contribution to L, between 0 and 1.",
    )
    parser.add_argument(
        "--ib",
        type=float,
        default=1.0,
        metavar="RATE",
        help="I contribution to B, between 0 and 1.",
    )
    parser.add_argument(
        "--yg",
        type=float,
        default=0.5,
        metavar="RATE",
        help="Y contribution to G, between 0 and 1.",
    )
    parser.add_argument(
        "--jr",
        type=float,
        default=0.25,
        metavar="RATE",
        help="J contribution to R, between 0 and 1.",
    )
    parser.add_argument(
        "--white",
        "-w",
        type=float,
        default=22.0,
        metavar="VALUE",
        help="White point in AB magnitude.",
    )
    parser.add_argument(
        "--stretch",
        "-a",
        type=float,
        default=28.0,
        metavar="FACTOR",
        help="Stretching factor in AB magnitude.",
    )
    parser.add_argument(
        "--offset",
        "-b",
        type=float,
        default=29.0,
        metavar="VALUE",
        help="Opposite of black point in AB magnitude.",
    )
    parser.add_argument(
        "--hue", type=float, default=-20, metavar="ANGLE", help="Hue shift"
    )
    parser.add_argument(
        "--saturation",
        type=float,
        default=1.2,
        metavar="GAIN",
        help="Saturation factor",
    )
    parser.add_argument(
        "--curves",
        type=str,
        nargs="*",
        default=["", "", "0.5: 0.55"],
        metavar="KNOTS",
        help="Curve spline knots for each channel (leave empty to disable).",
    )

    parser.set_defaults(func=run)


def run(args):

    print()

    transform = color.Transform(
        iyjh_zero_points=np.array(args.zero),
        iyjh_scaling=np.array(args.scaling),
        iyjh_fwhm=np.array(args.fwhm),
        sharpen_strength=args.sharpen,
        nir_to_l=args.nirl,
        i_to_b=args.ib,
        y_to_g=args.yg,
        j_to_r=args.jr,
        hue=args.hue,
        saturation=args.saturation,
        stretch=args.stretch,
        bw=np.array([args.offset, args.white]),
    )

    tile, slicing = io.parse_tile(args.tile)
    workdir = Path(args.workspace).expanduser() / tile
    name = args.output.replace("{tile}", tile)

    timer = Timer()

    print(f"Read IYJH image from: {workdir}")
    iyjh = io.read_iyjh(workdir, slicing, args.input)
    print(f"- Shape: {iyjh.shape[1]} x {iyjh.shape[2]}")
    timer.tic_print()

    print(f"Detect bad pixels")
    dead = mask.dead_pixels(iyjh)
    print(f"- Dead pixels: {', '.join(str(np.sum(channel)) for channel in dead)}")
    if "{step}" in name:
        path = workdir / name.replace("{step}", "mask")
        print(f"- Write: {path.name}")
        io.write_mask(dead, path)
    timer.tic_print()

    print(f"Inpaint dead pixels")
    iyjh[0] = mask.inpaint(iyjh[0], dead[0])
    # iyjh[0][dead[0]] = mask.resaturate(iyjh[0][dead[0]], np.max(iyjh[0]))
    nir_dead = dead[1] | dead[2] | dead[3]
    iyjh[1:] = mask.inpaint(iyjh[1:], nir_dead, 0)
    timer.tic_print()

    print(f"Sharpen channels")
    iyjh = color.sharpen(iyjh, transform.iyjh_fwhm / 2.355, transform.sharpen_strength)
    timer.tic_print()

    print(f"Stretch dynamic range")
    iyjh = color.stretch_iyjh(iyjh, transform)
    # print(f"- Medians: {', '.join(str(np.median(c)) for c in iyjh)}") # TODO use approximant
    timer.tic_print()
    # TODO save vstacked iyjh (crop if too high)

    print(f"Blend IYJH to RGB")
    lrgb = color.iyjh_to_lrgb(iyjh, transform)
    del iyjh
    rgb = color.lrgb_to_rgb(lrgb, transform)
    del lrgb
    if "{step}" in name or len(args.curves) == 0:
        # FIXME implement some Step to handle len(args.curves) == 0 case generically
        path = workdir / name.replace("{step}", "blended")
        print(f"- Write: {path.name}")
        io.write_rgb(rgb, path)
    timer.tic_print()

    # print(f"Inpaint hot pixels")
    # rgb[dead[0]] = mask.resaturate(rgb[dead[0]])
    # rgb = mask.inpaint(rgb, hot)
    # timer.tic_print()

    # if "{step}" in name:
    #     path = workdir / name.replace("{step}", "inpainted")
    #     print(f"- Write: {path.name}")
    #     io.write_rgb(rgb, path)
    #     timer.tic_print()

    if len(args.curves) > 0:
        print(f"Adjust curves")
        for i in range(len(args.curves)):
            knots = io.parse_map(args.curves[i])
            knots.insert(0, [0, 0])
            knots.append([1, 1])
            rgb[:, :, i] = color.adjust_curve(rgb[:, :, i], knots)
        path = workdir / name.replace("{step}", "adjusted")
        print(f"- Write: {path.name}")
        io.write_rgb(rgb, path)
        timer.tic_print()
