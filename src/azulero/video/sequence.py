# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from astropy import units as u
from astropy.coordinates import SkyCoord, Angle
from astropy.wcs import WCS
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import yaml

from azulero.tools import parsing


class MissingWCS(Exception):

    def __str__(self) -> str:
        return "Missing WCS parameters."


@dataclass
class Frame:
    """
    Viewport parameters for a single frame.
    """

    index: int  #: Frame index
    center: np.ndarray | Angle  #: Center in pixels or sky coordinates
    hfov: float | Angle  #: Horizontal field of view in pixels or angle of view
    roll: Angle  #: Viewport roll angle

    def planar(self, wcs: WCS, image_shape: tuple[int, int]):
        """
        Convert to planar parameters.
        """
        if self.hfov_is_solid_angle():
            left = self.center[0] + self.hfov / 2
            right = self.center[0] - self.hfov / 2
            dec = self.center[1]
            min = wcs.world_to_pixel(SkyCoord(ra=left, dec=dec, frame="icrs"))[0]
            max = wcs.world_to_pixel(SkyCoord(ra=right, dec=dec, frame="icrs"))[0]
            self.hfov = max - min
        if self.center_is_sky_coord():
            x, y = wcs.world_to_pixel(
                SkyCoord(ra=self.center[0], dec=self.center[1], frame="icrs")
            )
            self.center = np.array([x, image_shape[0] - y])
        return self

    def center_is_sky_coord(self):
        """
        Test whether the center is specified as sky coordinates.
        """
        return isinstance(self.center, Angle)

    def center_in_radec_degrees(self):
        """
        Get the RA and dec coordinates in degrees.
        """
        assert self.center_is_sky_coord()
        return np.array([float(self.center[0] / u.deg), float(self.center[1] / u.deg)])

    def hfov_is_solid_angle(self):
        """
        Test whether the field of view is specified as a horizontal field of view.
        """
        return isinstance(self.hfov, Angle)

    def hfov_in_degrees(self):
        """
        Get the field of view in degrees.
        """
        assert self.hfov_is_solid_angle()
        return float(self.hfov / u.deg)

    def roll_in_degrees(self):
        """
        Get the roll angle in degrees.
        """
        return float(self.roll / u.deg)

    def __repr__(self) -> str:
        res = f"{self.index}: "
        if self.center_is_sky_coord():
            res += f"({self.center[0] / u.deg:0.2f}°, {self.center[1] / u.deg:0.2f}°), "
        else:
            res += f"({self.center[0]:0.2f}, {self.center[1]:0.2f}), "
        if self.hfov_is_solid_angle():
            res += f"{self.hfov_in_degrees():0.2f}°, "
        else:
            res += f"{self.hfov:0.2f}, "
        res += f"{self.roll_in_degrees():0.2f}°"
        return res


@dataclass
class IndexedValue:
    index: int  #: Frame index
    value: Any  #: Parameter value


@dataclass
class KeyFrames:
    """
    Viewport parameters for key frames.
    """

    centers: list[IndexedValue]
    hfovs: list[IndexedValue]
    rolls: list[IndexedValue]

    def __len__(self):
        return len(self.centers)

    def append(self, frame, center, hfov, roll):
        """
        Append a key frame.
        """

        def _repeat(param):
            param.append(IndexedValue(frame, param[-1].value))

        def _append(param, value):
            param.append(IndexedValue(frame, value))

        if center is None:
            _repeat(self.centers)
        else:
            _append(self.centers, center)

        if hfov is None:
            _repeat(self.hfovs)
        elif not np.isnan(hfov):
            _append(self.hfovs, hfov)

        if roll is None:
            _repeat(self.rolls)
        elif not np.isnan(roll):
            _append(self.rolls, roll)

        return self


@dataclass
class RoamingContext:
    image_shape: tuple[int, int]
    video_format: tuple[int, int]
    fps: float
    wcs: WCS | None
    mode: str  #: "planar" or "spherical"


def read_key_frames(config: Path, context: RoamingContext) -> KeyFrames:
    """
    Read the key frames from a configuration file.
    """
    with open(config) as f:
        return parse_key_frames(yaml.safe_load(f), context)


def parse_key_frames(sequence: dict, context: RoamingContext) -> KeyFrames:
    """
    Parse the key frames in a dictionary.
    """
    res = KeyFrames([], [], [])
    frame = 0
    for step in sequence:
        if not "t" in step:
            center = parse_center(step["c"], context)
            add_knot(res, center)
        else:
            frame = parse_frame(step["t"], context.fps, frame)
            center = None if "c" not in step else parse_center(step["c"], context)
            hfov = None if "s" not in step else parse_hfov(step["s"], context)
            roll = None if "r" not in step else parse_roll(step["r"])
            res.append(frame, center, hfov, roll)
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


def _project(param_name, param, context: RoamingContext):
    """
    Call function `_{context.mode}_{param_name}({param}, {context})`,
    for example `_spherical_center(param, context)`.
    """
    func = globals()[f"_{context.mode}_{param_name}"]
    return func(param, context)


def parse_frame(text: str, fps: float, ref_frame: int) -> int:
    """
    Parse frame index or time.
    If last char is "f", return the value.
    If it is "s", multiply by `fps`.
    If the first char is "+", add `ref_frame`.
    """
    if match := parsing.match_suffix("f", text):
        value = int(match)
    elif match := parsing.match_suffix("s", text):
        value = int(float(match) * fps)
    else:
        raise parsing.ParseError("time", text)
    return value + ref_frame if text[0] == "+" else value


def parse_center(text: str, context: RoamingContext) -> np.ndarray | Angle:
    """
    Parse the center as sky or pixel coordinates.
    If there is no comma, parse an object name.
    Otherwise, try parsing spherical coordinates.
    Otherwise, each of them is parsed as a planar coordinate.
    """
    if "," not in text:
        coord = SkyCoord.from_name(text, parse=True)
        center = Angle([coord.ra, coord.dec])
    else:
        center = parsing.parse_lengths_or_angles(
            text, (context.image_shape[1], context.image_shape[0])
        )
    return _project("center", center, context)


def _planar_center(center: np.ndarray | Angle, context: RoamingContext) -> np.ndarray:
    if isinstance(center, Angle):
        if context.wcs is None:
            raise MissingWCS()
        xy = context.wcs.world_to_pixel(
            SkyCoord(ra=center[0], dec=center[1], frame="icrs")
        )
        return np.array(xy)
    return center


def _spherical_center(center: np.ndarray | Angle, context: RoamingContext) -> Angle:
    if isinstance(center, Angle):
        return center
    if context.wcs is None:
        raise MissingWCS()
    radec = context.wcs.pixel_to_world(*center)
    return Angle([radec.ra, radec.dec])


def parse_hfov(text: str, context: RoamingContext) -> float | Angle:
    """
    Parse the zoom.
    If last char is "w" (resp. "h"), zoom is relative to the image width (resp. height).
    If last char is "%", zoom is relative to the pixel size.
    Otherwise, the value is parsed as an angular horizontal field of view.
    """
    if text == "...":
        return np.nan
    if match := parsing.match_suffix("w", text):
        hfov = parsing.parse_length(match, context.image_shape[1])
    elif match := parsing.match_suffix("h", text):
        vfov = parsing.parse_length(match, context.image_shape[0])
        hfov = vfov * context.video_format[0] / context.video_format[1]
    elif match := parsing.match_suffix("%", text):
        hfov = 100 / float(match) * context.video_format[0]
    else:
        hfov = parsing.parse_length_or_angle(text)
    return _project("hfov", hfov, context)


def _planar_hfov(hfov: float | Angle, context: RoamingContext) -> float:
    if isinstance(hfov, float):
        return hfov
    if context.wcs is None:
        raise MissingWCS()
    # Using viewport center would be ideal but the difference is minimal at this scale
    half_height = context.image_shape[0] // 2
    half_width = context.image_shape[1] // 2
    center = context.wcs.pixel_to_world(half_width, half_height)
    top = center.dec + hfov / 2
    bottom = top - hfov
    max = context.wcs.world_to_pixel(SkyCoord(ra=center.ra, dec=top, frame="icrs"))[1]
    min = context.wcs.world_to_pixel(SkyCoord(ra=center.ra, dec=bottom, frame="icrs"))[
        1
    ]
    return max - min


def _spherical_hfov(hfov: float | Angle, context: RoamingContext) -> Angle:
    if isinstance(hfov, Angle):
        return hfov
    if context.wcs is None:
        raise MissingWCS()
    # Using viewport center would be ideal but the difference is minimal at this scale
    half_height = context.image_shape[0] // 2
    half_width = context.image_shape[1] // 2
    top = half_height + hfov // 2
    bottom = top - hfov
    max = context.wcs.pixel_to_world(half_width, top)
    min = context.wcs.pixel_to_world(half_width, bottom)
    return max.dec - min.dec


def parse_roll(text: str) -> float | Angle:
    """
    Parse the roll angle in degrees.
    If text ends with "pi", multiply the value by 180°.
    """
    if text == "...":
        return np.nan
    return parsing.parse_angle(text)
