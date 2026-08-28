# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Jean-Christophe Malapert and Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord

from azulero.providers import polygon


def test_meridian():

    footprint = polygon.ConvexSphericalPolygon([-1, 1, 1, -1], [10, 10, 20, 20])

    assert footprint.centroid in footprint

    assert SkyCoord(ra=0, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=180, dec=15, unit="deg") not in footprint


def test_antimeridian():

    footprint = polygon.ConvexSphericalPolygon([179, -179, -179, 179], [10, 10, 20, 20])

    assert footprint.centroid in footprint

    assert SkyCoord(ra=180, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=-180, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=0, dec=15, unit="deg") not in footprint


def test_edge():

    vertices = SkyCoord(ra=[0, 1, 1, 0], dec=[0, 0, 1, 1], unit="deg")
    footprint = polygon.ConvexSphericalPolygon(vertices.ra, vertices.dec)

    assert footprint.centroid in footprint

    for v in vertices:
        assert v in footprint

    ab = SkyCoord(ra=0.5, dec=0, unit="deg")
    bc = SkyCoord(ra=1, dec=0.5, unit="deg")
    cd = SkyCoord(ra=0.5, dec=1, unit="deg")
    da = SkyCoord(ra=0, dec=0.5, unit="deg")

    assert ab in footprint
    assert bc in footprint
    assert cd in footprint
    assert da in footprint
