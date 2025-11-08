# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np


@dataclass
class ControlPoint:
    frame: int
    x: float
    y: float
    z: float
    a_deg: float
    bc: str


def parse_sequence(sequence: dict, image_shape: list, fps: float, video_shape: list):
    res = []
    for step in sequence:
        frame = parse_frame(step, fps)
        cp = parse_params(frame, sequence[step], image_shape, video_shape)
        res.append(cp)
    # FIXME sort by frame
    return res


def parse_frame(text: str, fps: float):
    if text[-1] == "f":
        return int(text[:-1])
    if text[-1] == "s":
        return int(float(text[:-1]) * fps)
    raise ValueError(f"Unrecognized time: {text}")


def parse_params(frame: int, args: dict, image_shape: list, video_shape: list):
    x = None if "x" not in args else parse_coord(args["x"], image_shape[0])
    y = None if "y" not in args else parse_coord(args["y"], image_shape[1])
    z = None if "z" not in args else parse_zoom(args["z"], image_shape, video_shape)
    a = None if "a" not in args else parse_a_deg(args["a"])
    bc = None if "bc" not in args else parse_bc(args["bc"])
    return ControlPoint(frame, x, y, z, a, bc)


def parse_coord(text: str, image_extent: int):
    """
    Parse a coordinate.
    If last char is "%", coordinate is relative to the image extent.
    If value is negative, index backward.
    """
    if text[-1] == "%":
        px = float(text[:-1]) / 100 * image_extent
    else:
        px = float(text)
    if px < 0:
        px += image_extent
    return px


def parse_zoom(text: str, image_shape: list, video_shape: list):
    """
    Parse the zoom.
    If last char is "w" (resp. "h"), zoom is relative to the image width (resp. height).
    If last char is "%", zoom is a relative to the pixel size.
    """
    if text[-1] == "w":
        z = float(text[:-1]) * video_shape[0] / image_shape[0]
    elif text[-1] == "h":
        z = float(text[:-1]) * video_shape[1] / image_shape[1]
    elif text[-1] == "%":
        z = float(text[:-1]) / 100
    else:
        raise ValueError(f"Unrecognized zoom: {text}")
    return z


def parse_a_deg(text: str):
    """
    Parse the angle in degrees.
    If last char is "°", forward the value.
    If text ends with "pi", multiply by 180.
    """
    if text[-1] == "°":
        return float(text[:-1])
    elif text.endswith("pi"):
        return float(text[:-2]) * 180
    raise ValueError(f"Unrecognized angle: {text}")


def parse_bc(text: str):
    """
    Parse boundary conditions.
    """
    return text  # FIXME enumerate
