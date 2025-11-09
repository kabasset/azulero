# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
import numpy as np

from azulero import color  # TODO lerp to interp.py


@dataclass
class KeyFrame:
    frame: int
    center: np.ndarray
    z: float
    a_deg: float

    def __repr__(self) -> str:
        return f"{self.frame}: ({self.center[0]:0.1f}, {self.center[1]:0.1f}), {int(self.z * 100+0.5)}%, {self.a_deg}°"


def lerp(u, a, b):  # TODO implement ControPoint arithmetics and rely on color.lerp()
    if u == 0:
        return b
    if u == 1:
        return a
    frame = int(color.lerp(u, a.frame, b.frame) + 0.5)
    center = color.lerp(u, a.center, b.center)
    z = 1.0 / color.lerp(u, 1.0 / a.z, 1.0 / b.z)
    a_deg = color.lerp(u, a.a_deg, b.a_deg)
    return KeyFrame(frame, center, z, a_deg)


def parse_sequence(sequence: dict, image_shape: list, fps: float, video_shape: list):
    res = []
    frame = 0
    for step in sequence:
        frame = parse_frame(step, fps, frame)
        cp = parse_params(frame, sequence[step], image_shape, video_shape)
        res.append(cp)
    return _sanitize_sequence(res)


def _sanitize_sequence(sequence: list):
    # FIXME sort by frame
    for a, b in zip(sequence[:-1], sequence[1:]):
        if b.frame is None:
            b.frame = a.frame
        if b.center[0] is None:
            b.center[0] = a.center[0]
        if b.center[1] is None:
            b.center[1] = a.center[1]
        if b.z is None:
            b.z = a.z
        if b.a_deg is None:
            b.a_deg = a.a_deg
    return sequence


def parse_frame(text: str, fps: float, ref_frame: int):
    if text[-1] == "f":
        value = int(text[:-1])
    elif text[-1] == "s":
        value = int(float(text[:-1]) * fps)
    else:
        raise ValueError(f"Unrecognized time: {text}")
    return value + ref_frame if text[0] == "+" else value


def parse_params(frame: int, args: dict, image_shape: list, video_shape: list):
    x = None if "x" not in args else parse_coord(args["x"], image_shape[0])
    y = None if "y" not in args else parse_coord(args["y"], image_shape[1])
    z = None if "z" not in args else parse_zoom(args["z"], image_shape, video_shape)
    a = None if "a" not in args else parse_a_deg(args["a"])
    return KeyFrame(frame, np.array([x, y]), z, a)


def parse_coord(text: str, image_extent: int):
    """
    Parse a coordinate.
    If last char is "%", coordinate is relative to the image extent.
    If value is negative, index backward.
    """
    if text.endswith("px"):
        px = float(text[:-2])
    elif text[-1] == "%":
        px = float(text[:-1]) / 100 * image_extent
    else:
        ValueError(f"Unrecognized coordinate: {text}")
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
