# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Jean-Christophe Malapert and Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Sequence

from astropy.coordinates import SkyCoord
import numpy as np


class ConvexSphericalPolygon:
    """
    Convex spherical polygon.

    The polygon must be convex and cover less than one hemisphere.

    Args:
        vertices: Polygon vertices ordered either clockwise or counter-clockwise.
    """

    def __init__(self, vertices: Sequence[SkyCoord]):
        vectors = np.stack([_coord_to_vector(v) for v in vertices])
        self.normals = _compute_normals(vectors)

    def __contains__(self, coord: SkyCoord) -> bool:
        """
        Test whether a point lies inside the polygon.

        The algorithm uses spherical half-spaces:
        each polygon edge defines a plane passing through the sphere center.
        The point is inside the polygon if it lies on the same side of all edge planes.

        Args:
            point: Point vector.

        Returns:
            True if the point lies inside or on the edge of the polygon.
        """

        p = _coord_to_vector(coord)
        eps = np.finfo(float).eps
        return bool(np.all(self.normals @ p <= eps))


def _compute_normals(vertices: np.ndarray) -> np.ndarray:
    """
    Compute 3D outward-oriented face normals.

    Each normal corresponds to the plane containing the sphere center and edge endpoints.
    """

    n = len(vertices)

    center = np.sum(vertices, axis=0)

    out_normals = np.zeros([n, 3], dtype=float)

    for i in range(n):
        normal = np.cross(vertices[i], vertices[(i + 1) % n])
        out_normals[i] = normal if np.dot(normal, center) < 0 else -normal

    return np.asarray(out_normals, dtype=np.float64)


def _coord_to_vector(radec: SkyCoord) -> np.ndarray:
    """
    Convert RA/dec coordinates to a unit 3D vector.
    """

    assert radec.ra is not None and radec.dec is not None
    ra = np.deg2rad(radec.ra.degree)  # type: ignore
    dec = np.deg2rad(radec.dec.degree)  # type: ignore
    cos_dec = np.cos(dec)

    return np.asarray(
        [cos_dec * np.cos(ra), cos_dec * np.sin(ra), np.sin(dec)],
        dtype=np.float64,
    )
