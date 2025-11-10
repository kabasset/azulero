# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import cv2
import yaml

from azulero import sequence
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "roam",
        help="Make a video which pans and zooms between two points.",
        description=(
            "Supply an image, starting center point and zoom, and stopping center point and zoom."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=str,
        metavar="FILENAME",
        help="Input image file.",
    )
    parser.add_argument(
        "sequence",
        type=str,
        metavar="FILENAME",
        help="YAML configuration file which specifies the sequence of key frames.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output.mp4",
        metavar="FILENAME",
        help="Output video file.",
    )
    parser.add_argument(
        "--format",
        type=int,
        nargs=2,
        default=[1920, 1080],
        metavar=["WIDTH", "HEIGHT"],
        help="Video format",
    )
    parser.add_argument(
        "--fps", type=float, default=25, metavar="FPS", help="Frames per second."
    )

    parser.set_defaults(func=run)


def run(args):

    print()

    input = Path(args.workspace).expanduser() / args.input
    config = Path(args.sequence)
    output = Path(args.output)

    timer = Timer()

    print(f"Read input image: {input}")
    image = cv2.imread(input, cv2.IMREAD_COLOR)
    image_shape = image.shape[:2]
    print(f"- Format: {image_shape[0]} x {image_shape[1]}")
    timer.tic_print()

    print(f"Read sequence of key frames: {config}")
    with open(config) as f:
        params = sequence.load_frames_params(
            yaml.safe_load(f), image_shape, args.fps, args.format
        )
    centers = sequence.sin_sequence(params.centers)
    zooms_inv = sequence.sin_sequence(params.zooms_inv)
    angles_deg = sequence.sin_sequence(params.angles_deg)
    timer.tic_print()

    print(f"Generate frames")
    writer = cv2.VideoWriter(
        output, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, args.format
    )

    print(f"- Frame\tx\ty\tz\ta")
    for f, c, z, a in zip(range(len(centers)), centers, zooms_inv, angles_deg):
        print(f"- {f}\t{c[0]:0.1f}\t{c[1]:0.1f}\t{1.0/z:0.1f}\t{a:0.1f}")
        p = sequence.KeyFrame(0, c, 1.0 / z, a)
        frame = crop(image, p, args.format)
        writer.write(frame)

    writer.release()
    print(f"- Output written: {output}")
    timer.tic_print()


def crop(image, params, shape):
    # TODO optimize without rotation
    viewport = cv2.RotatedRect(params.center, np.array(shape) / params.z, params.a_deg)
    x, y, w, h = viewport.boundingRect()
    start = np.array([x, y])
    patch = image[y : y + h, x : x + w]
    rotation = cv2.getRotationMatrix2D(params.center - start, params.a_deg, params.z)
    rotated_image = cv2.warpAffine(patch, rotation, (w, h), flags=cv2.INTER_LINEAR)
    return cv2.getRectSubPix(rotated_image, shape, params.center - start)
