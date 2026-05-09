# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass
import numpy as np
from pathlib import Path

from azulero.image import color, io, mask
from azulero.tools.messaging import logger, read_pipe_args, write_pipe_args
from azulero.tools.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "process",
        help="Process MER channels to render a color image.",
        description="""
        Process MER channels:

        * Inpaint dead pixels;
        * Sharpen IYJH channels;
        * Stretch dynamic range with asinh function;
        * Blend IYJH channels into RGB and lightness (L) channels;
        * Boost intensity of saturated stars;
        * Shift hue and boost color saturation;
        * Adjust curves.
        """,
        usage="%(prog)s <workdirs> [options]",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "workdirs",
        type=str,
        nargs="*",
        default=read_pipe_args(),
        help="""
        Space separated list of workdirs relative to the workspace,
        optionally with slicing à-la NumPy, e.g. ``102160611[1500:7500,11500:17500]``.
        If no value is specified, the program will read ``stdin``.
        """,  # FIXME use {workspace}
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="{workspace}/{workdir}/{target}_{tile}_{step}.tiff",
        metavar="TEMPLATE",
        help="""
        Output path template, where: 

        * ``{workspace}`` is replaced with the workspace folder; 
        * ``{wordir}`` is replaced with the workdir folder relative to the workspace; 
        * ``{target}`` is replaced with the last part of the workdir or with 'Tile' if there is only one part; 
        * ``{tile}`` is replaced with the first part of the workdir; 
        * ``{step}`` is replaced with the processing step. 
          If ``{step}`` is not present in the template, 
          then intermediate steps are not saved.
        """,
    )
    parser.add_argument(
        "--zero",
        nargs=4,
        type=float,
        default=[24.5, 29.8, 30.1, 30.0],
        metavar=("ZP_I", "ZP_Y", "ZP_J", "ZP_H"),
        help="Zero points for each band.",  # FIXME read FITS header, keep this arg as the defaults
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=[2.2, 1.3, 1.2, 1.0],
        metavar=("GAIN_I", "GAIN_Y", "GAIN_J", "GAIN_H"),
        help="Scaling factors applied immediately to the IYJH bands for white balance.",
    )
    parser.add_argument(
        "--fwhm",
        nargs=4,
        type=float,
        default=[1.6, 3.5, 3.4, 3.5],
        metavar=("FWHM_I", "FWHM_Y", "FWHM_J", "FWHM_H"),
        help="FWHM for each band, used for sharpening.",
    )
    parser.add_argument(
        "--sharpen",
        type=float,
        default=0.5,
        metavar="STRENGTH",
        help="Strength of the sharpening. Set to 0 to disable sharpening.",
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
        default=22.5,
        metavar="AB_MAG",
        help="White point in AB magnitude.",
    )
    parser.add_argument(
        "--stretch",
        "-a",
        type=float,
        default=27.0,
        metavar="AB_MAG",
        help="Stretching factor in AB magnitude.",
    )
    parser.add_argument(
        "--offset",
        "-b",
        type=float,
        default=28.5,
        metavar="AB_MAG",
        help="Opposite of black point in AB magnitude.",
    )
    parser.add_argument(
        "--hue",
        type=float,
        default=-20,
        metavar="ANGLE",
        help="Hue shift in degrees.",
    )
    parser.add_argument(
        "--saturation",
        type=float,
        default=1.2,
        metavar="GAIN",
        help="Saturation factor.",
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


def render_path_for_step(template, step):
    return Path(template.format(step=step))


@dataclass
class IOs:
    workspace: Path
    input_pattern: str
    channel_names: list
    output_template: str


def run(args):

    curves = []
    for i in range(len(args.curves)):
        knots = io.parse_map(args.curves[i])
        if knots:
            first = knots[0]
            if first[0] != 0 and first[1] != 0:
                knots.insert(0, (0, 0))
            last = knots[-1]
            if last[0] != 1 and last[1] != 1:
                knots.append((1, 1))
        else:
            knots = [(0, 0), (1, 1)]
        curves.append(knots)

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
        curves=curves[::-1],  # RGB to BGR
    )

    ios = IOs(
        workspace=args.workspace,
        input_pattern=args.input,
        channel_names=args.channels,
        output_template=args.output,
    )

    for target in args.workdirs:
        process_target(ios, target, transform)


def process_target(ios: IOs, target: str, transform: color.Transform):

    logger.header(1, f"Target: {target}", linebreaks=[1, 0])

    target, slicing = io.parse_target(target)
    parts = Path(target).parts
    tile = parts[0] if len(parts) > 1 else "Tile"
    name = parts[-1]
    if slicing:
        slicing_str = f"{slicing[0].start or ''}:{slicing[0].stop or ''},{slicing[1].start or ''}:{slicing[1].stop or ''}"
    else:
        slicing_str = ""
    workdir = Path(ios.workspace).expanduser() / target
    template = ios.output_template.format(
        workspace=ios.workspace,
        workdir=target,
        target=name,
        tile=tile,
        slicing=slicing_str,
        step="{step}",
    )

    timer = Timer()

    logger.header(2, f"Read IYJH image from: {workdir}")
    iyjh = io.read_iyjh(workdir, slicing, ios.input_pattern, ios.channel_names)
    logger.bullet(f"Shape: {iyjh.shape[1]} x {iyjh.shape[2]}")
    wcs_filename = io.find_wcs(workdir, ios.input_pattern)
    if wcs_filename:
        wcs = io.read_wcs(wcs_filename, slicing)
    else:
        wcs = None
        logger.warning(f"No WCS found.")
    path = render_path_for_step(template, "wcs").with_suffix(".yaml")
    timer.tic_log()

    logger.header(2, f"Detect bad pixels")
    dead = mask.dead_pixels(iyjh)
    logger.bullet(f"Dead pixels: {', '.join(str(np.sum(channel)) for channel in dead)}")
    if "{step}" in template:
        path = render_path_for_step(template, "mask")
        logger.bullet(f"Write: {path.name}")
        io.write_mask(dead, path)
    timer.tic_log()

    logger.header(2, f"Inpaint dead pixels")
    iyjh[0] = mask.inpaint(iyjh[0], dead[0])
    print(np.min(iyjh[0]), np.max(iyjh[0]))
    nir_dead = dead[1] | dead[2] | dead[3]
    iyjh[1:] = mask.inpaint(iyjh[1:], nir_dead, 0)
    timer.tic_log()

    logger.header(2, f"Sharpen channels")
    iyjh = color.sharpen(iyjh, transform.iyjh_fwhm / 2.355, transform.sharpen_strength)
    timer.tic_log()

    logger.header(2, f"Stretch dynamic range")
    iyjh = color.stretch_iyjh(iyjh, transform)
    # iyjh[0][dead[0]] = mask.resaturate(iyjh[0][dead[0]])
    timer.tic_log()
    # TODO save vstacked iyjh (crop if too high)

    logger.header(2, f"Blend IYJH to RGB")
    lbgr = color.iyjh_to_lbgr(iyjh, transform)
    del iyjh
    bgr = color.lbgr_to_bgr(lbgr, transform)
    del lbgr
    if "{step}" in template or len(transform.curves) == 0:
        # FIXME implement some Step to handle len(args.curves) == 0 case generically
        path = render_path_for_step(template, "blended")
        logger.bullet(f"Write: {path.name}")
        io.write_normalized_bgr(path, bgr, wcs)
    timer.tic_log()

    if len(transform.curves) > 0:
        logger.header(2, f"Adjust curves")
        for i in range(len(transform.curves)):
            bgr[:, :, i] = color.adjust_curve(bgr[:, :, i], transform.curves[i])
        path = render_path_for_step(template, "adjusted")
        logger.bullet(f"Write: {path.name}")
        io.write_normalized_bgr(path, bgr, wcs)
        timer.tic_log()

    write_pipe_args([path])
