# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import cv2
import yaml

from azulero import sequence, widgets
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "roam",
        help="Create a video which pans and zooms in an image.",
        description=(
            "Supply an image, specify viewport position and parameters at given times."
            "They will be interpolated to render a smooth roaming video."
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
        "--fps", type=float, default=24, metavar="FPS", help="Frames per second."
    )
    parser.add_argument(
        "--scale",
        type=str,
        nargs="*",
        default=None,
        metavar=["LENGTH", "TEXT"],
        help="Scale length in image pixels, and text above",
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
    print(f"- Shape: {image_shape[0]} x {image_shape[1]}")
    timer.tic_print()

    print(f"Read sequence of key frames: {config}")
    with open(config) as f:
        params = sequence.load_frames_params(
            yaml.safe_load(f), image_shape, args.fps, args.format
        )
    print(f"- Key frames: {len(params)}")
    centers = sequence.sin_sequence(params.centers)
    zooms_inv = sequence.sin_sequence(params.zooms_inv)
    angles_deg = sequence.sin_sequence(params.angles_deg)
    print(f"- Total frames: {len(centers)}")
    timer.tic_print()

    if args.scale is None:
        scale = widgets.Scale(width=0, text="")
    elif len(args.scale) == 0:
        scale = widgets.Scale(width=600, text="1 arcmin")
    elif len(args.scale) == 1:
        scale = widgets.Scale(width=int(args.scale[0]), text="")
    elif len(args.scale) == 2:
        scale = widgets.Scale(width=int(args.scale[0]), text=args.scale[1])

    print(f"Generate frames")
    writer = cv2.VideoWriter(
        output, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, args.format
    )

    print(f"- Frame\tx\ty\tz (%)\ta (°)")
    for f, c, z, a in zip(range(len(centers)), centers, zooms_inv, angles_deg):
        print(f"- {f}\t{c[0]:0.1f}\t{c[1]:0.1f}\t{100.0/z:0.1f}\t{a:0.1f}")
        p = sequence.KeyFrame(0, c, 1.0 / z, a)
        frame = crop(image, p, args.format)
        if scale.width > 0:
            scale.draw(frame, 100.0 / z)
        writer.write(frame)

    writer.release()
    print(f"- Output written: {output}")
    timer.tic_print()


def crop(image: np.ndarray, params, format):
    center = params.center
    viewport_format = np.array(format, dtype=float) / params.z
    a = params.a_deg % 360
    viewport = cv2.RotatedRect(params.center, viewport_format, -a)
    x0, y0, w, h = viewport.boundingRect()
    vertical = w < h
    if vertical:
        # OpenCV unhappy!
        x0, y0, w, h = y0, x0, h, w
        image = np.swapaxes(image, 0, 1)
        a = 90 - a
        center = np.flip(center)
    x1 = x0 + w
    y1 = y0 + h
    if x0 < 0:
        print(f"- WARNING: min(x) < 0 ({x0})")
        x0 = 0
    if y0 < 0:
        print(f"- WARNING: max(y) min < 0 ({y0})")
        y0 = 0
    if x1 > image.shape[1]:
        print(f"- WARNING: max(x) > {image.shape[1]-1} ({x1-1})")
        x1 = image.shape[0]
    if y1 > image.shape[0]:
        print(f"- WARNING: max(y) > {image.shape[0]-1} ({y1-1})")
        y1 = image.shape[1]
    offset = np.array([x0, y0])
    patch = image[y0:y1, x0:x1]
    rotation = cv2.getRotationMatrix2D(center - offset, a, params.z)
    rotation_format = (w, h)
    rotated_image = cv2.warpAffine(
        patch, rotation, rotation_format, flags=cv2.INTER_LINEAR
    )
    res = cv2.getRectSubPix(rotated_image, format, center - offset)
    if vertical:
        return np.flipud(res)
    return res
