# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Jean-Christophe Malapert and Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import Angle, SkyCoord
import numpy as np


class ConvexSphericalPolygon:
    """
    Convex spherical polygon.

    The polygon must be convex and cover less than one hemisphere.

    Args:
        ra: Right ascension of the polygon vertices ordered either clockwise or counter-clockwise.
        dec: Declination of the polygon vertices ordered either clockwise or counter-clockwise.
    """

    def __init__(self, ra, dec):
        xyz = radec_to_xyz(ra, dec)
        self._centroid = np.sum(xyz, axis=1)
        self._normals = _compute_normals(xyz, self._centroid)

    @classmethod
    def from_geojson(cls, geometry: dict):
        """
        Instantiate a polygon from a GeoJSON polygon geometry.
        """
        ra, dec = map(np.array, zip(*geometry["coordinates"][0]))
        return cls(ra, dec)

    @property
    def centroid(self):
        return xyz_to_radec(self._centroid)

    def __contains__(self, p: SkyCoord | np.ndarray) -> bool:
        """
        Test whether a point lies inside the polygon.

        The algorithm uses spherical half-spaces:
        each polygon edge defines a plane passing through the sphere center.
        The point is inside the polygon if it lies on the same side of all edge planes.

        Args:
            p: The coordinate or 3D vector to be tested.

        Returns:
            True if the point lies inside or on the edge of the polygon.
        """

        if isinstance(p, SkyCoord):
            p = radec_to_xyz(p.ra, p.dec)
        eps = np.finfo(float).eps
        for n in self._normals:
            if np.dot(n, p) > eps:
                return False
        return True


def _compute_normals(xyz: np.ndarray, inside: np.ndarray) -> np.ndarray:
    """
    Compute 3D outward-oriented face normals.

    Each normal corresponds to the plane containing the sphere center and edge endpoints.
    """

    n = xyz.shape[1]
    out_normals = np.zeros([n, 3], dtype=float)

    for i in range(n):
        normal = np.cross(xyz[:, i], xyz[:, (i + 1) % n])
        out_normals[i] = normal if np.dot(normal, inside) <= 0 else -normal

    return out_normals


def radec_to_xyz(ra, dec) -> np.ndarray:
    """
    Convert RA/dec coordinates into unit 3D vectors.
    """

    if isinstance(ra, Angle):
        ra = ra.radian
    else:
        ra = np.deg2rad(ra)
    if isinstance(dec, Angle):
        dec = dec.radian
    else:
        dec = np.deg2rad(dec)

    cos_dec = np.cos(dec)
    x = cos_dec * np.cos(ra)
    y = cos_dec * np.sin(ra)
    z = np.sin(dec)
    return np.stack([x, y, z])


def xyz_to_radec(xyz: np.ndarray) -> SkyCoord:
    """
    Convert 3D vectors into RA/dec coordinates.
    """
    x, y, z = xyz
    ra = np.arctan2(y, x)
    dec = np.arctan2(z, np.sqrt(x * x + y * y))
    return SkyCoord(ra=ra, dec=dec, unit="rad")


class ConvexPolygon:
    """
    Convex spherical polygon.

    The polygon must be convex and cover less than one hemisphere.

    Args:
        ra, dec: RA/dec of the polygon vertices ordered either clockwise or counter-clockwise.
    """

    def __init__(self, ra, dec):
        self._xyz = radec_to_xyz(ra, dec)
        self._centroid = np.sum(self._xyz, axis=1)

    @property
    def centroid(self):
        """
        Centroid coordinates.
        """
        return xyz_to_radec(self._centroid)

    def __len__(self):
        """
        Vertex count.
        """
        return self._xyz.shape[1]

    def __contains__(self, p):
        """
        Test whether a point lies inside the polygon.
        """
        if isinstance(p, SkyCoord):
            p = radec_to_xyz(p.ra, p.dec)
        n = len(self)
        tol = np.finfo(float).eps
        for i in range(n):
            # Great-circle plane normal
            normal = np.cross(self._xyz[:, i], self._xyz[:, (i + 1) % n])
            # Point outward
            if np.dot(normal, self._centroid) > 0:
                normal = -normal
            if np.dot(normal, p) > tol:
                return False
        return True
