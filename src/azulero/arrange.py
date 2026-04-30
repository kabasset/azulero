# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import cv2
import numpy as np
from pathlib import Path

from azulero.tools.timing import Timer
from azulero.tools.messaging import logger, read_pipe_args, write_pipe_args


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "arrange",
        help="Assemble a grid of images.",
        description=("Crop or pad images and assemble them into a grid."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "images",
        type=str,
        nargs="*",
        default=read_pipe_args(),
        help="Paths to the images, relative to the workspace.",
    )
    parser.add_argument(
        "--columns",
        "-n",
        type=int,
        default=0,
        help="Maximum number of columns, or 0.",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="min,min",
        metavar=("WIDTH,HEIGHT"),
        help="Format of each image in the grid.",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=6,
        metavar="PIXELS",
        help="Number of pixels around images.",
    )
    parser.add_argument(
        "--background",
        type=int,
        default=0,
        metavar="COLOR",
        help="Value of the background pixels",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="PATH",
        default="{workspace}/collage_{first}_{last}.png",
        help=(
            "Output collage path template, where: ",
            "{workspace} is replaced by the workspace path, ",
            "{first} and {last} are respectively replaced by the first and last file stems in the input list",
        ),
    )

    parser.set_defaults(func=run)


def run(args):

    timer = Timer()
    workspace = Path(args.workspace).expanduser()

    columns = min(len(args.images), args.columns) if args.columns else len(args.images)
    rows = (len(args.images) - 1) // columns + 1

    filenames = [workspace / n for n in args.images]
    logger.header(1, f"Read {len(filenames)} image{'s' if len(filenames) > 1 else ''}")
    images = [cv2.imread(f) for f in filenames]
    w, h = parse_format(args.format, images)
    logger.bullet(f"Crop: {w} x {h}")
    timer.tic_log()

    logger.header(1, f"Prepare canvas")
    width = args.margin * (columns + 1) + w * columns
    height = args.margin * (rows + 1) + h * rows
    logger.bullet(f"Format: {width} x {height}")
    canvas = np.full([height, width, 3], args.background, dtype=np.uint8)
    # FIXME support RGBA
    timer.tic_log()

    logger.header(1, f"Blit images")
    for r in range(rows):
        for c in range(columns):
            i = c + r * columns
            if i >= len(filenames):
                break
            logger.bullet(f"{r}, {c}: {filenames[i]}")
            x = args.margin * (c + 1) + w * c
            y = args.margin * (r + 1) + h * r
            blit_centered(canvas[y : y + h, x : x + w, :], images[i])
    output = args.output.format(
        workspace=args.workspace, first=filenames[0].stem, last=filenames[-1].stem
    )
    logger.bullet(1, f"Save collage: {output}")
    cv2.imwrite(output, canvas)
    timer.tic_log()

    write_pipe_args([output])


def parse_format(arg, images):
    aggs = {"min": min, "max": max, "median": lambda l: int(np.median(l))}
    widths = [i.shape[1] for i in images]
    heights = [i.shape[0] for i in images]
    format = arg.split(",")
    if len(format) == 1:
        if format[0].isdigit():
            w = h = int(format[0])
        else:
            w = h = aggs[format[0]](widths + heights)
    else:
        if format[0].isdigit():
            w = int(format[0])
        else:
            w = aggs[format[0]](widths)
        if format[1].isdigit():
            h = int(format[1])
        else:
            h = aggs[format[1]](heights)
    return w, h


def blit_centered(canvas, image):
    shape = [min(bg, fg) for bg, fg in zip(canvas.shape, image.shape)]
    bg_slice = slice_centered(canvas.shape, shape)
    fg_slice = slice_centered(image.shape, shape)
    canvas[bg_slice] = image[fg_slice]


def slice_centered(outer_shape, inner_shape):
    margin = (np.array(outer_shape) - inner_shape) // 2
    return tuple(slice(m, m + s) for m, s in zip(margin, inner_shape))
