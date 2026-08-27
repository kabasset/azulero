# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Jean-Christophe Malapert and Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from typing import Sequence

from astropy.coordinates import Angle, SkyCoord
import numpy as np


class ConvexSphericalPolygon:
    """
    Convex spherical polygon.

    The polygon must be convex and cover less than one hemisphere.

    Args:
        vertices: Polygon vertices ordered either clockwise or counter-clockwise.
    """

    def __init__(self, vertices: Sequence[SkyCoord]):
        vectors = [_coord_to_vector(v) for v in vertices]
        self._centroid = np.sum(vectors, axis=0)
        self._normals = _compute_normals(vectors, self._centroid)

    @classmethod
    def from_geojson(cls, geometry: dict):
        """
        Instantiate a polygon from a GeoJSON polygon geometry.
        """
        vertices = [
            SkyCoord(ra=ra, dec=dec, unit="deg")
            for ra, dec in geometry["coordinates"][0]
        ]
        return cls(vertices)

    @property
    def centroid(self):
        return _vector_to_coord(self._centroid)

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
        return bool(np.all(self._normals @ p <= eps))


def _compute_normals(vectors: Sequence[np.ndarray], inside: np.ndarray) -> np.ndarray:
    """
    Compute 3D outward-oriented face normals.

    Each normal corresponds to the plane containing the sphere center and edge endpoints.
    """

    n = len(vectors)
    out_normals = np.zeros([n, 3], dtype=float)

    for i in range(n):
        normal = np.cross(vectors[i], vectors[(i + 1) % n])
        out_normals[i] = normal if np.dot(normal, inside) <= 0 else -normal

    return out_normals


def _coord_to_vector(radec: SkyCoord) -> np.ndarray:
    """
    Convert RA/dec coordinates into a unit 3D vector.
    """

    assert isinstance(radec.ra, Angle) and isinstance(radec.dec, Angle)
    ra = radec.ra.radian
    dec = radec.dec.radian
    cos_dec = np.cos(dec)

    return np.asarray(
        [cos_dec * np.cos(ra), cos_dec * np.sin(ra), np.sin(dec)],
        dtype=np.float64,
    )


def _vector_to_coord(vector: np.ndarray) -> SkyCoord:
    """
    Convert a 3D vector into RA/dec coordinates.
    """
    x, y, z = vector
    ra = np.arctan2(y, x)
    dec = np.arctan2(z, np.sqrt(x * x + y * y))
    return SkyCoord(ra=ra, dec=dec, unit="rad")
