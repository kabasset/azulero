# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import cv2
from scipy.spatial.transform import Rotation
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from azulero.video.sequence import Frame

def capture_frame(image : np.ndarray, wcs: WCS, video_format: tuple[int, int], frame: Frame):
    hfov = frame.hfov_in_degrees()
    vfov = 2 * np.atan(np.tan(hfov / 2) * video_format[1] / video_format[0])
    fov = np.deg2rad([hfov, vfov])
    xyz = _xyzpers(fov, np.deg2rad(frame.center), video_format, frame.orientation)
    u, v = _xyz2uv(xyz)
    ra = 360 - np.rad2deg(u)
    dec = np.rad2deg(v)
    x, y = wcs.world_to_pixel(SkyCoord(ra, dec, unit="deg", frame="icrs"))
    x = np.nan_to_num(x, nan=-1).astype(np.float32)
    y = np.nan_to_num(image.shape[0] - y -1, nan=-1).astype(np.float32)
    x, y = cv2.convertMaps(
            x,
            y,
            cv2.CV_16SC2,
            nninterpolation=False,
        )
    # FIXME image pyramid
    return cv2.remap(image, x, y, interpolation=cv2.INTER_CUBIC)


def _xyzpers(
    fov: tuple[float,float],
    center: SkyCoord,
    video_format: tuple[int, int],
    orientation: float,
) -> np.ndarray:
    out = np.ones((video_format[1], video_format[0], 3), np.float32)
    x_max = np.tan(fov[0] / 2)
    y_max = np.tan(fov[1] / 2)
    x_ticks = np.linspace(-x_max, x_max, num=video_format[0], dtype=np.float32)
    y_ticks = np.linspace(-y_max, y_max, num=video_format[1], dtype=np.float32)
    out[..., :2] = np.stack(np.meshgrid(x_ticks, -y_ticks), -1)
    Rx = rotation_matrix(center[1], 0)
    Ry = rotation_matrix(center[0], 1)
    Ri = rotation_matrix(orientation, np.array([0.0, 0.0, 1.0]).dot(Rx).dot(Ry))

    return out.dot(Rx).dot(Ry).dot(Ri).astype(np.float32)


def _xyz2uv(xyz: np.array) -> tuple[np.array, np.array]:
    """Transform cartesian (x,y,z) to spherical(r, u, v), and only outputs (u, v).

    Parameters
    ----------
    xyz: ndarray
        An array object in shape of [..., 3].

    Returns
    -------
    out: ndarray
        An array object in shape of [..., 2],
        any point i of this array is in [-pi, pi].

    Notes
    -----
    In this project, e2c calls utils._xyz2uv(xyz) where:

        * xyz is in [-0.5, 0.5] x [-0.5, 0.5] x [-0.5, 0.5]
        * u is in [-pi, pi]
        * v is in [-pi/2, pi/2]
        * any point i of output array is in [-pi, pi] x [-pi/2, pi/2].
    """
    x = xyz[..., 0:1]  # Keep dimensions but avoid copy
    y = xyz[..., 1:2]
    z = xyz[..., 2:3]
    u = np.arctan2(x, z)
    c = np.hypot(x, z)
    v = np.arctan2(y, c)
    return u, v


def rotation_matrix(rad: float, ax: int | np.ndarray | list):
    if isinstance(ax, int):
        ax = (np.arange(3) == ax).astype(float)
    ax = np.array(ax)
    return Rotation.from_rotvec(rad * ax).as_matrix()
