# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from astropy.wcs import WCS
import numpy as np
from pathlib import Path

from azulero.image import color, io, mask
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools import parsing
from azulero.tools.timing import Timer
from azulero.tools.workspace import Workspace

default_transform = color.Transform()
default_workspace = Workspace()


def add_parser(subparsers, help):
    parser = subparsers.add_parser(
        "process",
        help=help,
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
        optionally with slicing à-la NumPy, e.g. `102160611[1500:7500,11500:17500]`.
        If no value is specified, the program will read `stdin`.

        If the path to a FITS file is specified instead of a workdir,
        extensions named after the channels will be used instead of individual files.
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=default_workspace.output_template,
        metavar="TEMPLATE",
        help="""
        Output path template, where: 

        * `{workspace}` is replaced with the workspace folder; 
        * `{workdir}` is replaced with the workdir folder relative to the workspace; 
        * `{0}, {1}, ...` are replaced with the parts of the workdir; 
        * `{step}` is replaced with the processing step. 
          If `{step}` is not present in the template, 
          then intermediate steps are not saved.
        """,
    )
    parser.add_argument(
        "--zero",
        nargs=4,
        type=float,
        default=default_transform.iyjh_zero_points,
        metavar=("ZP_I", "ZP_Y", "ZP_J", "ZP_H"),
        help="Zero points for each band.",  # FIXME read FITS header, keep this arg as the defaults
    )
    parser.add_argument(
        "--scaling",
        nargs=4,
        type=float,
        default=default_transform.iyjh_scaling,
        metavar=("GAIN_I", "GAIN_Y", "GAIN_J", "GAIN_H"),
        help="Scaling factors applied immediately to the IYJH bands for white balance.",
    )
    parser.add_argument(
        "--overshoot",
        type=float,
        default=default_transform.neg_overshoot,
        metavar="RATE",
        help=(
            "Negative overshooting wrt. null flux: "
            "0 means an output null value is an input null flux, "
            "while 1 means an output null value is the offset (which leaves more room for postprocessing)."
        ),
    )
    parser.add_argument(
        "--fwhm",
        nargs=4,
        type=float,
        default=default_transform.iyjh_fwhm,
        metavar=("FWHM_I", "FWHM_Y", "FWHM_J", "FWHM_H"),
        help="FWHM for each band, used for sharpening.",
    )
    parser.add_argument(
        "--sharpen",
        type=float,
        default=default_transform.sharpen_strength,
        metavar="STRENGTH",
        help="Strength of the sharpening. Set to 0 to disable sharpening.",
    )
    parser.add_argument(
        "--nirl",
        type=float,
        default=default_transform.nir_to_l,
        metavar="RATE",
        help="NIR contribution to L, between 0 and 1.",
    )
    parser.add_argument(
        "--ib",
        type=float,
        default=default_transform.i_to_b,
        metavar="RATE",
        help="I contribution to B, between 0 and 1.",
    )
    parser.add_argument(
        "--yg",
        type=float,
        default=default_transform.y_to_g,
        metavar="RATE",
        help="Y contribution to G, between 0 and 1.",
    )
    parser.add_argument(
        "--jr",
        type=float,
        default=default_transform.j_to_r,
        metavar="RATE",
        help="J contribution to R, between 0 and 1.",
    )
    parser.add_argument(
        "--white",
        "-w",
        type=float,
        default=default_transform.bw[1],
        metavar="AB_MAG",
        help="White point in AB magnitude, or 0 to enable experimental auto-tuning.",
    )
    parser.add_argument(
        "--stretch",
        "-a",
        type=float,
        default=default_transform.stretch,
        metavar="AB_MAG",
        help="Stretching factor in AB magnitude.",
    )
    parser.add_argument(
        "--offset",
        "-b",
        type=float,
        default=default_transform.bw[0],
        metavar="AB_MAG",
        help="Opposite of black point in AB magnitude.",
    )
    parser.add_argument(
        "--hue",
        type=float,
        default=default_transform.hue,
        metavar="ANGLE",
        help="Hue shift in degrees.",
    )
    parser.add_argument(
        "--saturation",
        type=float,
        default=default_transform.saturation,
        metavar="GAIN",
        help="Saturation factor.",
    )
    parser.add_argument(
        "--curves",
        type=str,  # argparse bug: parse_map incompatible with ArgumentDefaultsHelpFormatter
        nargs="*",
        default=[parsing.dump_map(c) for c in default_transform.bgr_curves[::-1]],
        metavar="KNOTS",
        help="Curve spline knots for each channel (leave empty to disable).",
    )

    parser.set_defaults(**parse_envargs("process"), func=run)


def dump_slicing(slicing):
    if slicing is None:
        return ""
    items = [f"{s.start or ''}:{s.stop or ''}" for s in slicing]
    return ",".join(items)


def render_path_for_step(template, step):
    return Path(template.format(step=step))


def run(args):

    transform = color.Transform(
        iyjh_zero_points=args.zero,
        iyjh_scaling=args.scaling,
        iyjh_fwhm=args.fwhm,
        sharpen_strength=args.sharpen,
        nir_to_l=args.nirl,
        i_to_b=args.ib,
        y_to_g=args.yg,
        j_to_r=args.jr,
        hue=args.hue,
        saturation=args.saturation,
        stretch=args.stretch,
        bw=(args.offset, args.white),
        neg_overshoot=args.overshoot,
        bgr_curves=tuple(parsing.parse_map(c) for c in args.curves[::-1]),  # RGB to BGR
    )

    ios = Workspace.from_args(args)

    for target in args.workdirs:
        process_target(ios, target, transform)


def process_target(ios: Workspace, arg: str, transform: color.Transform):

    logger.header(1, f"Target: {arg}", linebreaks=[1, 0])

    target, slicing = parsing.parse_target(arg)
    parts = list(Path(target).parts)
    if Path(target).is_file():
        parts[-1] = Path(target).stem  # For MEF files, remove extensions
    workdir = ios.workspace / target

    template = parsing.render_template(
        ios.output_template,
        *parts,
        workspace=ios.workspace,
        workdir=target,
        slicing=dump_slicing(slicing),
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
    timer.tic_log()

    process_iyjh(iyjh, wcs, transform, template, ios, timer)


def process_iyjh(
    iyjh: np.ndarray,
    wcs: WCS,
    transform: color.Transform = color.Transform(),
    template: str = "",
    ios: Workspace = Workspace(),
    timer: Timer = Timer(),
) -> np.ndarray:

    logger.header(2, f"Detect bad pixels")
    dead = mask.dead_pixels(iyjh)
    logger.bullet(f"Bad pixels: {', '.join(str(np.sum(c)) for c in dead)}")
    if "{step}" in template:
        path = render_path_for_step(template, "mask")
        logger.bullet(f"Write: {path.name}")
        io.write_mask(dead, path)
    timer.tic_log()

    logger.header(2, f"Inpaint dead pixels")
    dead = mask.clear_corners(dead)
    iyjh[0] = mask.inpaint(iyjh[0], dead[0])
    nir_dead = dead[1] | dead[2] | dead[3]
    iyjh[1:] = mask.inpaint(iyjh[1:], nir_dead, 0)
    logger.bullet(f"Inpainted pixels: {', '.join(str(np.sum(c)) for c in dead)}")
    timer.tic_log()

    logger.header(2, f"Sharpen channels")
    iyjh = color.sharpen(
        iyjh, np.array(transform.iyjh_fwhm) / 2.355, transform.sharpen_strength
    )
    timer.tic_log()

    logger.header(2, f"Stretch dynamic range")
    iyjh = color.stretch_iyjh(iyjh, transform)
    timer.tic_log()
    # TODO save vstacked iyjh (crop if too high)

    logger.header(2, f"Blend IYJH to RGB")
    lbgr = color.iyjh_to_lbgr(iyjh, transform)
    del iyjh
    bgr = color.lbgr_to_bgr(lbgr, transform)
    del lbgr
    bgr[dead[0]] = mask.resaturate(bgr[dead[0]])
    if "{step}" in template or len(transform.bgr_curves) == 0:
        path = render_path_for_step(template, "blended")
        logger.bullet(f"Write: {path.name}")
        io.write_normalized_bgr(path, bgr, wcs)
    timer.tic_log()

    if len(transform.bgr_curves) > 0:  # FIXME always 3, check values
        logger.header(2, f"Adjust curves")
        for i in range(len(transform.bgr_curves)):
            bgr[:, :, i] = color.adjust_curve(bgr[:, :, i], transform.bgr_curves[i])
        path = render_path_for_step(template, "adjusted")
        logger.bullet(f"Write: {path.name}")
        io.write_normalized_bgr(path, bgr, wcs)
        timer.tic_log()

    if path.suffix:
        write_pipe_args([ios.relative_to_workspace(path)])

    return bgr
