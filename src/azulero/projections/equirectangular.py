# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import cv2
from scipy.spatial.transform import Rotation


class Projection:
    """
    Equirectangular to planar projection, adapted from py360convert.
    """

    def __init__(self, x: np.ndarray, y: np.ndarray):
        # Add 1 to the coordinates to compensate for the 1 pixel padding.
        self.x, self.y = cv2.convertMaps(
            x + 1,
            y + 1,
            cv2.CV_16SC2,
            nninterpolation=False,
        )

    def __call__(self, img: np.ndarray) -> np.ndarray:
        img = img.astype(np.float32)
        padded = self._pad(img)
        return cv2.remap(padded, self.x, self.y, interpolation=3)

    def _pad(self, img: np.ndarray) -> np.ndarray:
        """Adds 1 pixel of padding around entire image."""
        w = img.shape[1]
        padded = np.pad(img, ((1, 1), (1, 1)), mode="empty")
        padded[0, 1:-1] = np.roll(img[[0]], w // 2, axis=1)
        padded[-1, 1:-1] = np.roll(img[[-1]], w // 2, axis=1)
        padded[:, 0] = padded[:, -2]
        padded[:, -1] = padded[:, 1]
        return padded

    @classmethod
    def from_perspective(
        cls,
        fov: tuple[float, float],
        center: tuple[float, float],
        orientation: float,
        image_shape: tuple[int, int],
        video_format: tuple[int, int],
    ):
        xyz = _xyzpers(*fov, *center, (video_format[1], video_format[0]), orientation)
        u, v = _xyz2uv(xyz)
        x, y = uv2coor(u, v, *image_shape)
        return cls(x, y)


def _xyzpers(
    h_fov: float,
    v_fov: float,
    u: float,
    v: float,
    out_hw: tuple[int, int],
    in_rot: float,
) -> np.ndarray:
    out = np.ones((*out_hw, 3), np.float32)
    x_max = np.tan(h_fov / 2)
    y_max = np.tan(v_fov / 2)
    x_rng = np.linspace(-x_max, x_max, num=out_hw[1], dtype=np.float32)
    y_rng = np.linspace(-y_max, y_max, num=out_hw[0], dtype=np.float32)
    out[..., :2] = np.stack(np.meshgrid(-x_rng, y_rng), -1)
    Rx = rotation_matrix(v, 0)
    Ry = rotation_matrix(-u, 1)
    Ri = rotation_matrix(in_rot, np.array([0, 0, 1.0]).dot(Rx).dot(Ry))

    return out.dot(Rx).dot(Ry).dot(Ri).astype(np.float32)


def _xyz2uv(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
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


def uv2coor(
    u: np.ndarray, v: np.ndarray, h: int, w: int
) -> tuple[np.ndarray, np.ndarray]:
    """Transform spherical(r, u, v) into equirectangular(x, y).

    Assume that u has range 2pi and v has range pi.
    The coordinate of the equirectangular is from (0.5, 0.5) to (h-0.5, w-0.5).

    Parameters
    ----------
    uv: ndarray
        An array object in shape of [..., 2].
    h: int
        Height of the equirectangular image.
    w: int
        Width of the equirectangular image.

    Returns
    -------
    out: ndarray
        An array object in shape of [..., 2].

    Notes
    -----
    In this project, e2c calls utils.uv2coor(uv, h, w) where:

        * uv is in [-pi, pi] x [-pi/2, pi/2]
        * x is in [-0.5, w-0.5]
        * y is in [-0.5, h-0.5]
    """
    x = (-u / (2 * np.pi) + 0.5) * w - 0.5
    y = (v / np.pi + 0.5) * h - 0.5
    return x, y


def rotation_matrix(rad: float, ax: int | np.ndarray | list):
    if isinstance(ax, int):
        ax = (np.arange(3) == ax).astype(float)
    ax = np.array(ax)
    return Rotation.from_rotvec(rad * ax).as_matrix()
