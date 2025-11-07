# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import cv2

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
        "--to",
        type=float,
        nargs=3,
        default=[0.5, 0.5, 1.0],
        metavar="STOP",
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
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=5,
        metavar="SECONDS",
        help="Duration in seconds.",
    )

    parser.set_defaults(func=run)


def run(args):

    print()

    input = Path(args.workspace).expanduser() / args.input
    output = Path(args.output)

    timer = Timer()

    print(f"Read input image: {input}")
    image = cv2.imread(input, cv2.IMREAD_COLOR)
    image_shape = image.shape[:2]
    print(f"- Format: {image_shape[0]} x {image_shape[1]}")
    timer.tic_print()

    print(f"Generate frames")
    num_frames = int(args.fps * args.duration)
    video_shape = args.format
    video_ratio = video_shape[0] / video_shape[1]
    start = vars(args)["from"]
    stop = args.to
    print(f"{start} -> {stop}")
    frames = []
    for alpha in np.sin(np.linspace(0, 1, num_frames) * np.pi - np.pi / 2) / 2 + 0.5:
        rx = stop[0] * alpha + start[0] * (1 - alpha)  # FIXME lerp()
        ry = stop[1] * alpha + start[1] * (1 - alpha)  # FIXME lerp()
        x = int(image_shape[1] * rx)
        y = int(image_shape[0] * ry)
        zoom = 1.0 / (
            1.0 / stop[2] * alpha + 1.0 / start[2] * (1 - alpha)
        )  # FIXME lerp()
        print(f"- {alpha:0.2f}: {x}, {y}, {zoom}")
        if image_shape[1] / image_shape[0] > video_ratio:
            h = int(video_shape[0] / zoom)
            w = int(h * video_ratio)
        else:
            w = int(video_shape[1] / zoom)
            h = int(w / video_ratio)
        cropped = crop(image, x, y, w, h)
        scaled = cv2.resize(cropped, dsize=video_shape, interpolation=cv2.INTER_LINEAR)
        frames.append(scaled)
    timer.tic_print()

    print(f"Write output video: {output}")
    writer = cv2.VideoWriter(
        output, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, video_shape
    )
    for frame in frames:
        writer.write(frame)
    writer.release()
    timer.tic_print()


def crop(image, x, y, w, h):
    x0, y0 = max(0, x - w // 2), max(0, y - h // 2)
    x1, y1 = x0 + w, y0 + h
    return image[y0:y1, x0:x1]
