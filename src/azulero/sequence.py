# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from collections import OrderedDict
from turtle import right
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from dataclasses import dataclass
import scipy.interpolate as interp
import numpy as np

from azulero import color  # TODO lerp to interp.py


@dataclass
class Frame:
    """
    Viewport parameters for a single frame.
    """

    index: int  #: Frame index
    center: np.ndarray | SkyCoord  #: Viewport center in pixels or sky coordinates
    zoom: float | u.Quantity  #: Viewport zoom as ratio or horizontal field of view
    angle: u.Quantity  #: Viewport angle

    def planar(self, wcs: WCS, video_format):
        """
        Convert to planar parameters.
        """
        if self.zoom_is_hfov():
            left = self.center.copy()
            left.ra -= self._hfov_in_degrees() / 2
            right = self.center.copy()
            right.ra += self._hfov_in_degrees() / 2
            min = wcs.world_to_pixel(left)[0]
            max = wcs.world_to_pixel(right)[0]
            fov = max - min
            self.zoom = fov / video_format[0]
        if self.center_is_sky_coord():
            self.center = wcs.world_to_pixel(self.center)
        return self

    def center_is_sky_coord(self):
        """
        Test whether the center is specified as sky coordinates.
        """
        return isinstance(self.center, SkyCoord)

    def zoom_is_hfov(self):
        """
        Test whether the zoom is specified as a horizontal field of view.
        """
        if isinstance(self.zoom, u.Quantity):
            assert (self.zoom / u.deg).is_unity()
            return True
        return False

    def _hfov_in_degrees(self):
        """
        Get the zoom in degrees.
        """
        assert self.zoom_is_hfov()
        return float(self.zoom / u.deg)

    def __repr__(self) -> str:
        res = f"{self.index}: "
        if self.center_is_sky_coord():
            res += f"({self.center.ra}°, {self.center.dec}°), "
        else:
            res += f"({self.center[0]}, {self.center[1]}), "
        if self.zoom_is_hfov():
            res += f"{self._hfov_in_degrees()}°, "
        else:
            res += f"{int(self.zoom * 100+0.5)}%, "
        res += f"{float(self.angle / u.deg)}°"
        return res


@dataclass
class KeyFrames:
    """
    Viewport parameters for key frames.
    """

    centers: OrderedDict
    zooms: OrderedDict
    angles_deg: OrderedDict

    def __len__(self):
        return len(self.centers)

    def __iadd__(self, frame):
        """
        Append a key frame.
        """

        def _last_value(param):
            return next(reversed(param.values()))

        def _repeat(param):
            param[frame] = _last_value(param)

        center = frame.center
        if center is None:
            _repeat(self.centers)
        else:
            self.centers[frame] = center  # TODO test compatibility

        zoom = frame.zoom
        if zoom is None:
            _repeat(self.zooms)
        elif not np.isnan(zoom):
            self.zooms[frame] = zoom

        angle = frame.angle
        if angle is None:
            _repeat(self.angles_deg)
        elif not np.isnan(angle):
            self.angles_deg[frame] = angle

        return self


def read_key_frames(sequence: list, image_shape: list, fps: float, video_format: list):
    res = KeyFrames({}, {}, {})
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
            z = (
                None
                if "z" not in step
                else parse_zoom(step["z"], image_shape, video_format)
            )
            a = None if "a" not in step else parse_angle(step["a"])
            res.append(frame, center, z, a)
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
        # if wcs is None:
        #     x = (-float(x) + 180) / 360 * image_shape[1]
        #     y = (float(y) + 90) / 180 * image_shape[0]
        #     return x, y
        # else:
        return SkyCoord(
            ra=float(x) * u.degree,
            dec=float(y) * u.degree,
            frame="icrs",
        )
        # x, y = wcs.world_to_pixel(coords)
        # return x, image_shape[0] - y
    x = _parse_planar_coord(text_xy[0], image_shape[1])
    y = _parse_planar_coord(text_xy[1], image_shape[0])
    return x, y


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
    elif match := match_suffix("°", text):
        z = float(match) * u.deg
    else:
        raise ValueError(f"Unrecognized zoom: {text}")
    return z


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
