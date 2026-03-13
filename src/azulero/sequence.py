# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import scipy.interpolate as interp
import yaml


@dataclass
class Frame:
    """
    Viewport parameters for a single frame.
    """

    index: int  #: Frame index
    center: np.ndarray | SkyCoord  #: Center in pixels or sky coordinates
    hfov: float | u.Quantity  #: Horizontal field of view in pixels or solid angle
    orientation: u.Quantity  #: Viewport orientation angle

    def planar(self, wcs: WCS, image_shape: tuple[int, int]):
        """
        Convert to planar parameters.
        """
        if self.hfov_is_solid_angle():
            left = self.center.copy()
            left.ra -= self.hfov_in_degrees() / 2
            right = self.center.copy()
            right.ra += self.hfov_in_degrees() / 2
            min = wcs.world_to_pixel(left)[0]
            max = wcs.world_to_pixel(right)[0]
            self.hfov = max - min
        if self.center_is_sky_coord():
            x, y = wcs.world_to_pixel(self.center)
            self.center = np.array([x, image_shape[0] - y])
        return self

    def center_is_sky_coord(self):
        """
        Test whether the center is specified as sky coordinates.
        """
        return isinstance(self.center, SkyCoord)

    def center_in_radec_degrees(self):
        """
        Get the RA and dec coordinates in degrees.
        """
        assert self.center_is_sky_coord()
        return np.array([float(self.center.ra / u.deg), float(self.center.dec / u.deg)])

    def hfov_is_solid_angle(self):
        """
        Test whether the field of view is specified as a horizontal field of view.
        """
        if isinstance(self.hfov, u.Quantity):
            assert (self.hfov / u.deg).is_unity()
            return True
        return False

    def hfov_in_degrees(self):
        """
        Get the field of view in degrees.
        """
        assert self.hfov_is_solid_angle()
        return float(self.hfov / u.deg)

    def orientation_in_degrees(self):
        """
        Get the orientation in degrees.
        """
        return float(self.orientation / u.deg)

    def __repr__(self) -> str:
        res = f"{self.index}: "
        if self.center_is_sky_coord():
            res += f"({self.center.ra}°, {self.center.dec}°), "
        else:
            res += f"({self.center[0]}, {self.center[1]}), "
        if self.hfov_is_solid_angle():
            res += f"{self.hfov_in_degrees()}°, "
        else:
            res += f"{self.hfov}, "
        res += f"{self.orientation_in_degrees()}°"
        return res


@dataclass
class FrameParam:
    index: int  #: Frame index
    value: Any  #: Parameter value


@dataclass
class KeyFrames:
    """
    Viewport parameters for key frames.
    """

    centers: list[FrameParam]
    hfovs: list[FrameParam]
    orientations: list[FrameParam]

    def __len__(self):
        return len(self.centers)

    def append(self, frame, center, hfov, orientation):
        """
        Append a key frame.
        """

        def _repeat(param):
            param.append(FrameParam(frame, param[-1].value))

        def _append(param, value):
            param.append(FrameParam(frame, value))

        if center is None:
            _repeat(self.centers)
        else:
            _append(self.centers, center)

        if hfov is None:
            _repeat(self.hfovs)
        elif not np.isnan(hfov):
            _append(self.hfovs, hfov)

        if orientation is None:
            _repeat(self.orientations)
        elif not np.isnan(orientation):
            _append(self.orientations, orientation)

        return self


def read_key_frames(config: Path, image_shape: list, fps: float, video_format: list):
    """
    Read the key frames from a configuration file.
    """
    with open(config) as f:
        return parse_key_frames(yaml.safe_load(f), image_shape, fps, video_format)


def parse_key_frames(sequence: dict, image_shape: list, fps: float, video_format: list):
    """
    Parse the key frames in a dictionary.
    """
    res = KeyFrames([], [], [])
    frame = 0
    for step in sequence:
        if not "t" in step:
            center = parse_center((step["x"], step["y"]), image_shape)
            add_knot(res, center)
        else:
            frame = parse_frame(step["t"], fps, frame)
            if "x" not in step and "y" not in step:
                center = None
            else:
                center = parse_center((step["x"], step["y"]), image_shape)
            hfov = (
                None
                if "z" not in step
                else parse_hfov(step["z"], image_shape, video_format)
            )
            orientation = None if "a" not in step else parse_angle(step["a"])
            res.append(frame, center, hfov, orientation)
    return res


def add_knot(sequence, center):
    """
    Add a spline not to the center trajectory.
    """
    knots = sequence.centers[-1].value
    if isinstance(knots, list):
        sequence.centers[-1].value.append(center)
    else:
        sequence.centers[-1].value = [knots, center]


def sin_sequence(key_frames: list[FrameParam]):
    """
    Interpolate parameters over a sequence of frames with sine sampling.
    """
    res = []
    for start, stop in zip(key_frames[:-1], key_frames[1:]):
        if isinstance(start.value, list):
            res += [*sin_spline(start, stop)]
        else:
            res += sin_step(start, stop)
    # TODO prepend first value if first frame > 0
    return res


def sin_step(start: FrameParam, stop: FrameParam):
    """
    Linearly interpolate parameters between two frames with sine sampling.
    """
    stop_value = stop.value[0] if isinstance(stop.value, list) else stop.value
    return [
        lerp(1 - u, start.value, stop_value)
        for u in sin_sampling(start.index, stop.index)
    ]


def lerp(x, a, b):  # FIXME to interp.py
    if x == 0:
        return b
    if x == 1:
        return a
    if isinstance(a, SkyCoord) or isinstance(b, SkyCoord):
        return SkyCoord(lerp(x, a.ra, b.ra), lerp(x, a.dec, b.dec), frame="icrs")
    return x * a + (1 - x) * b


def sin_spline(start: FrameParam, stop: FrameParam):
    """
    Spline-interpolate trajectory between knots with sine sampling.
    """
    knots = np.stack([*start.value, stop.value])
    b = interp.make_interp_spline(
        np.linspace(0, 1, len(knots)), knots, k=min(3, len(knots) - 1)
    )
    u = sin_sampling(start.index, stop.index)
    return b(u)


def sin_sampling(start, stop):
    """
    Sine sampling between two bounds.

    Args:
        start: Start frame index.
        stop: Stop frame index.

    Returns:
        An array of sine-spaced values between 0 and 1.
    """
    return np.sin(np.linspace(0, 1, stop - start) * np.pi - np.pi / 2) / 2 + 0.5


def match_suffix(suffix: str, text: str):
    """
    Test whether a string ends with some suffix.
    If it does, return the beginning of the string.
    Otherwise, return `None`.
    """
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


def parse_center(text_xy: tuple, image_shape: tuple):
    """
    Parse the center as sky or pixel coordinates.
    If the values of both `x` and `y` end with "°", they are considered sky coordinates.
    Otherwise, each of them is parsed as a planar coordinate.
    """
    if (x := match_suffix("°", text_xy[0])) and (y := match_suffix("°", text_xy[1])):
        return SkyCoord(
            ra=float(x) * u.degree,
            dec=float(y) * u.degree,
            frame="icrs",
        )
    x = _parse_planar_coord(text_xy[0], image_shape[1])
    y = _parse_planar_coord(text_xy[1], image_shape[0])
    return np.array([x, y])


def _parse_planar_coord(text: str, image_extent):
    """
    Parse a planar coordinate.
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


def parse_hfov(text: str, image_shape: list, video_format: list):
    """
    Parse the zoom.
    If last char is "w" (resp. "h"), zoom is relative to the image width (resp. height).
    If last char is "%", zoom is relative to the pixel size.
    If last char is "°", zoom is a horizontal field of view of an equirectangular input.
    """
    if text == "...":
        return np.nan
    if match := match_suffix("w", text):
        return float(match) * image_shape[1]
    if match := match_suffix("h", text):
        vfov = float(match) * image_shape[0]
        return vfov * video_format[0] / video_format[1]
    if match := match_suffix("%", text):
        return float(match) / 100 * video_format[0]
    if match := match_suffix("°", text):
        return float(match) * u.deg
    raise ValueError(f"Unrecognized zoom: {text}")


def parse_angle(text: str):
    """
    Parse the angle in degrees.
    If last char is "°", forward the value.
    If text ends with "pi", multiply by 180.
    """
    if text == "...":
        return np.nan
    if match := match_suffix("°", text):
        return float(match) * u.deg
    elif match := match_suffix("pi", text):
        return float(match) * 180 * u.deg
    raise ValueError(f"Unrecognized angle: {text}")
