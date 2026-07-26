# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import cv2
import numpy as np
from pathlib import Path

from azulero.tools.timing import Timer
from azulero.tools.messaging import (
    logger,
    parse_envargs,
    read_pipe_args,
    write_pipe_args,
)
from azulero.tools import parsing
from azulero.tools.workspace import Workspace


def add_parser(subparsers, help):
    parser = subparsers.add_parser(
        "arrange",
        help=help,
        description="Crop, pad or scale images and assemble them into a grid.",
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
        metavar="WIDTH,HEIGHT",
        help="Format of each image in the grid.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1,
        metavar="FACTOR",
        help="Scale factor, or 0 to fit the image size to the cell size.",
    )
    parser.add_argument(
        "--margin",
        default="1%",
        metavar="SPACE",
        help="Margin around the grid in pixels or percentage of the maximum image extent.",
    )
    parser.add_argument(
        "--gap",
        default="1%",
        metavar="SPACE",
        help="Margin between cells in pixels or percentage of the maximum image extent.",
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
        help="""
        Output collage path template, where:

        * ``{workspace}`` is replaced by the workspace path,
        * ``{first}`` and ``{last}`` are respectively replaced by the first and last file stems in the input list.
        """,
    )

    parser.set_defaults(**parse_envargs("arrange"), func=run)


def run(args):

    timer = Timer()
    ios = Workspace.from_args(args)

    columns = min(len(args.images), args.columns) if args.columns else len(args.images)
    rows = (len(args.images) - 1) // columns + 1

    filenames = [ios.workspace / f for f in args.images]
    logger.header(1, f"Read {len(filenames)} image{'s' if len(filenames) > 1 else ''}")
    images = [scale(cv2.imread(f), args.scale) for f in filenames]
    w, h = parse_format(args.format, images)
    if args.scale == 0:
        images = [scale_to_fit(i, (h, w)) for i in images]
    logger.bullet(f"Crop: {w} x {h}")
    timer.tic_log()

    logger.header(1, f"Prepare canvas")
    gap = parse_spacing(args.gap, max(w, h))
    margin = parse_spacing(args.margin, max(w, h))
    width = (columns - 1) * gap + columns * w + 2 * margin
    height = (rows - 1) * gap + rows * h + 2 * margin
    logger.bullet(f"Format: {width} x {height}")
    canvas = np.full([height, width, 3], args.background, dtype=np.uint8)
    # TODO support RGBA
    timer.tic_log()

    logger.header(1, f"Blit images")
    for r in range(rows):
        for c in range(columns):
            i = c + r * columns
            if i >= len(filenames):
                break
            logger.bullet(f"{r}, {c}: {filenames[i]}")
            x = margin + (gap + w) * c
            y = margin + (gap + h) * r
            blit_centered(canvas[y : y + h, x : x + w, :], images[i])
    output = Path(
        ios.output_template.format(
            workspace=ios.workspace, first=filenames[0].stem, last=filenames[-1].stem
        )
    )
    logger.bullet(f"Write: {output.name}")
    cv2.imwrite(output, canvas)
    timer.tic_log()

    write_pipe_args([ios.relative_to_workspace(output)])


def scale(image: np.ndarray, factor: float):
    if factor <= 0 or factor == 1:
        return image
    return cv2.resize(
        image, dsize=None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC
    )


def scale_to_fit(image: np.ndarray, shape: tuple[int, int]):
    ratio = np.max(np.array(shape) / image.shape[:2])
    return scale(image, ratio)


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
    # TODO Add small tolerance to prevent ugly gaps or scaling up or down by factors close to 1
    # For example, if `w - 1 in widths`, reduce the size (be careful when `len(format) == 1`)
    return w, h


def parse_spacing(text: str, reference: int):
    return int(parsing.parse_length(text, reference) + 0.5)


def blit_centered(canvas, image):
    shape = [min(bg, fg) for bg, fg in zip(canvas.shape, image.shape)]
    bg_slice = slice_centered(canvas.shape, shape)
    fg_slice = slice_centered(image.shape, shape)
    canvas[bg_slice] = image[fg_slice]


def slice_centered(outer_shape, inner_shape):
    margin = (np.array(outer_shape) - inner_shape) // 2
    return tuple(slice(m, m + s) for m, s in zip(margin, inner_shape))
