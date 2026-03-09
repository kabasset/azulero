# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from dataclasses import dataclass
import scipy.interpolate as interp
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


@dataclass
class KeyValue:
    frame: int
    value: object


@dataclass
class KeyFrames:
    centers: list
    zooms_inv: list
    angles_deg: list

    def __len__(self):
        return len(self.centers)

    def append(self, frame, center, zoom, angle):
        if center[0] is None or center[1] is None:  # FIXME can there be a single None?
            self.centers.append(KeyValue(frame, self.centers[-1].value))
        else:
            self.centers.append(KeyValue(frame, center))
        if zoom is None:
            self.zooms_inv.append(KeyValue(frame, self.zooms_inv[-1].value))
        elif not np.isnan(zoom):
            self.zooms_inv.append(KeyValue(frame, 1.0 / zoom))
        if angle is None:
            self.angles_deg.append(KeyValue(frame, self.angles_deg[-1].value))
        elif not np.isnan(angle):
            self.angles_deg.append(KeyValue(frame, angle))
        return self


def load_frames_params(
    sequence: list, image_shape: list, fps: float, video_format: list, wcs: WCS | None
):
    res = KeyFrames([], [], [])
    frame = 0
    for step in sequence:
        if not "t" in step:
            x, y = parse_coords((step["x"], step["y"]), image_shape, wcs)
            add_knot(res, x, y)
        else:
            frame = parse_frame(step["t"], fps, frame)
            if "x" not in step and "y" not in step:
                x, y = None, None
            else:
                x, y = parse_coords((step["x"], step["y"]), image_shape, wcs)
            z = (
                None
                if "z" not in step
                else parse_zoom(step["z"], image_shape, video_format)
            )
            a = None if "a" not in step else parse_a_deg(step["a"])
            res.append(frame, np.array([x, y]), z, a)
    return res


def add_knot(sequence, x, y):
    knots = sequence.centers[-1].value
    if isinstance(knots, list):
        sequence.centers[-1].value.append(np.array([x, y]))
    else:
        sequence.centers[-1].value = [knots, np.array([x, y])]


def sin_sequence(keys_values: list):
    """
    Interpolate parameters over a sequence of frames with sine sampling.
    """
    res = []
    for start, stop in zip(keys_values[:-1], keys_values[1:]):
        if isinstance(start.value, list):
            res += [*sin_spline(start, stop)]
        else:
            res += sin_step(start, stop)
    # FIXME prepend first value if first frame > 0
    return res


def sin_step(start, stop):
    """
    Linearly interpolate parameters between two frames with sine sampling.
    """
    stop_value = stop.value if not isinstance(stop.value, list) else stop.value[0]
    return [
        color.lerp(1 - u, start.value, stop_value)
        for u in sin_sampling(start.frame, stop.frame)
    ]


def sin_spline(start, stop):
    """
    Spline-interpolate trajectory between knots with sine sampling.
    """
    knots = np.stack([*start.value, stop.value])
    b = interp.make_interp_spline(
        np.linspace(0, 1, len(knots)), knots, k=min(3, len(knots) - 1)
    )
    u = sin_sampling(start.frame, stop.frame)
    return b(u)


def sin_sampling(start, stop):
    """
    Sine sampling between two bounds.
    """
    return np.sin(np.linspace(0, 1, stop - start) * np.pi - np.pi / 2) / 2 + 0.5


def match_suffix(suffix: str, text: str):
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return None


def parse_frame(text: str, fps: float, ref_frame: int):
    """
    Parse frame index or time.
    If last char is "f", return the value.
    If it is "s", multiply by `fps`.
    If the first char is "+", add `ref_frame`.
    """
    if match := match_suffix("f", text):
        value = int(match)
    elif match := match_suffix("s", text):
        value = int(float(match) * fps)
    else:
        raise ValueError(f"Unrecognized time: {text}")
    return value + ref_frame if text[0] == "+" else value


def parse_coords(text_xy: tuple, image_shape: tuple, wcs: WCS | None):
    if (match_x := match_suffix("°", text_xy[0])) and (
        match_y := match_suffix("°", text_xy[1])
    ):
        if wcs is None:
            x = (-float(match_x) + 180) / 360 * image_shape[1]
            y = (float(match_y) + 90) / 180 * image_shape[0]
            return x, y
        else:
            coords = SkyCoord(
                ra=float(match_x) * u.degree,
                dec=float(match_y) * u.degree,
                frame="icrs",
            )
            x, y = wcs.world_to_pixel(coords)
            return x, image_shape[0] - y
    x = _parse_planar_coord(text_xy[0], image_shape[1])
    y = _parse_planar_coord(text_xy[1], image_shape[0])
    return x, y


def _parse_planar_coord(text: str, image_extent):
    """
    Parse a coordinate.
    If last char is "%", coordinate is relative to the image extent.
    If value is negative, index backward.
    """
    if value := match_suffix("px", text):
        px = float(value)
    elif value := match_suffix("%", text):
        px = float(value) / 100 * image_extent
    else:
        raise ValueError(f"Unrecognized coordinate: {text}")
    if px < 0:
        px += image_extent
    return px


def parse_zoom(text: str, image_shape: list, video_format: list):
    """
    Parse the zoom.
    If last char is "w" (resp. "h"), zoom is relative to the image width (resp. height).
    If last char is "%", zoom is relative to the pixel size.
    If last char is "°", zoom is a horizontal field of view of an equirectangular input.
    """
    if text == "...":
        return np.nan
    if match := match_suffix("w", text):
        z = video_format[0] / image_shape[1] / float(match)
    elif match := match_suffix("h", text):
        z = video_format[1] / image_shape[0] / float(match)
    elif match := match_suffix("%", text):
        z = float(match) / 100
    elif match := match_suffix("°", text):  # FIXME adapt to WCS?
        z = -1 / float(match)
    else:
        raise ValueError(f"Unrecognized zoom: {text}")
    return z


def parse_a_deg(text: str):
    """
    Parse the angle in degrees.
    If last char is "°", forward the value.
    If text ends with "pi", multiply by 180.
    """
    if text == "...":
        return np.nan
    if match := match_suffix("°", text):  # FIXME adapt to WCS (wrt North)?
        return float(match)
    elif match := match_suffix("pi", text):
        return float(match) * 180
    raise ValueError(f"Unrecognized angle: {text}")
