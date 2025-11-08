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
        help="YAML configuration file which specifies the sequence of control points.",
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
        "--from",
        type=float,
        nargs=3,
        default=[0.5, 0.5, 1.0],
        metavar="START",
        help="Starting center point and zoom.",
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

    print(f"Read sequence of control points: {config}")
    with open(config) as f:
        steps = sequence.parse_sequence(
            yaml.safe_load(f), image_shape, args.fps, args.format
        )
    timer.tic_print()

    roamer = Roamer(image, args.fps, args.format)
    writer = cv2.VideoWriter(
        output, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, args.format
    )

    for start, stop in zip(steps[:-1], steps[1:]):
        print(f"Generate frames {start.frame} to {stop.frame}.")
        frames = roamer.roam(start, stop)
        timer.tic_print()
        print(f"Write {len(frames)} frames.")
        for f in frames:
            writer.write(f)
        timer.tic_print()

    print(f"Write output video: {output}")
    writer.release()
    timer.tic_print()


class Roamer(object):

    def __init__(self, image, fps, shape):
        self.image = image
        self.image_shape = image.shape[:2]
        self.fps = fps
        self.video_shape = shape
        self.video_ratio = shape[0] / shape[1]

    def roam(self, start: sequence.ControlPoint, stop: sequence.ControlPoint):
        res = []
        for u in self._sampling(start.frame, stop.frame):
            # TODO shortcut if stop == start
            params = sequence.lerp(1 - u, start, stop)
            if self.image_shape[1] / self.image_shape[0] > self.video_ratio:
                h = int(self.video_shape[0] / params.z)
                w = int(h * self.video_ratio)
            else:
                w = int(self.video_shape[1] / params.z)
                h = int(w / self.video_ratio)
            cropped = crop(self.image, params, self.video_shape)
            res.append(cropped)
        return res

    def _sampling(self, start, stop):
        return np.sin(np.linspace(0, 1, stop - start) * np.pi - np.pi / 2) / 2 + 0.5


def crop(image, params, shape):
    viewport = cv2.RotatedRect(params.center, np.array(shape) / params.z, params.a_deg)
    x, y, w, h = viewport.boundingRect()
    start = np.array([x, y])
    patch = image[y : y + h, x : x + w]
    rotation = cv2.getRotationMatrix2D(params.center - start, params.a_deg, params.z)
    rotated_image = cv2.warpAffine(patch, rotation, (w, h), flags=cv2.INTER_LINEAR)
    return cv2.getRectSubPix(rotated_image, shape, params.center - start)
