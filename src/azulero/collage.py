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
        "collage",
        help="Assemble a grid of images.",
        description=("Assemble a grid of images of same shapes."),
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
        type=int,
        nargs=2,
        default=[600, 600],
        metavar=("WIDTH", "HEIGHT"),
        help="Format of each image in the grid.",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=6,
        metavar="PIXELS",
        help="Number of pixels between images.",
    )
    parser.add_argument(
        "--background",
        type=str,
        default=None,
        metavar="COLOR",
        help="Color name of comma-separated components of the margins (None for transparent or black)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="PATH",
        help="Output collage path, relative to the workspace.",
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
    logger.info(f"- Crop: {args.format[0]} x {args.format[1]}")
    timer.tic_log()

    logger.header(1, f"Prepare canvas")
    width = args.margin * (columns + 1) + args.format[0] * columns
    height = args.margin * (rows + 1) + args.format[1] * rows
    logger.info(f"- Format: {width} x {height}")
    canvas = np.zeros([height, width, 3], dtype=np.uint8)  # FIXME adapt dtype?
    # FIXME fill color
    timer.tic_log()

    logger.header(1, f"Blit images")
    for r in range(rows):
        for c in range(columns):
            i = c + r * columns
            if i >= len(filenames):
                break
            logger.info(f"- {r}, {c}: {filenames[i]}")
            x = args.margin * (c + 1) + args.format[0] * c
            y = args.margin * (r + 1) + args.format[1] * r
            logger.info(f"- to: {x}, {y}")
            canvas[y : y + args.format[1], x : x + args.format[0], :] = crop(
                images[i], args.format
            )
    timer.tic_log()

    logger.header(1, f"Save collage: {args.output}")
    cv2.imwrite(args.output, canvas)
    timer.tic_log()

    write_pipe_args([args.output])


def crop(image, format):
    return image[0 : format[1], 0 : format[0], :]  # FIXME center
