# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Jean-Christophe Malapert and Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import SkyCoord

from azulero.providers import polygon


def test_meridian():

    footprint = polygon.ConvexSphericalPolygon(
        [
            SkyCoord(ra=-1, dec=10, unit="deg"),
            SkyCoord(ra=1, dec=10, unit="deg"),
            SkyCoord(ra=1, dec=20, unit="deg"),
            SkyCoord(ra=-1, dec=20, unit="deg"),
        ]
    )

    assert SkyCoord(ra=0, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=180, dec=15, unit="deg") not in footprint


def test_antimeridian():

    footprint = polygon.ConvexSphericalPolygon(
        [
            SkyCoord(ra=179, dec=10, unit="deg"),
            SkyCoord(ra=-179, dec=10, unit="deg"),
            SkyCoord(ra=-179, dec=20, unit="deg"),
            SkyCoord(ra=179, dec=20, unit="deg"),
        ]
    )

    assert SkyCoord(ra=180, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=-180, dec=15, unit="deg") in footprint
    assert SkyCoord(ra=0, dec=15, unit="deg") not in footprint


def test_edge():

    a = SkyCoord(ra=0, dec=0, unit="deg")
    b = SkyCoord(ra=1, dec=0, unit="deg")
    c = SkyCoord(ra=1, dec=1, unit="deg")
    d = SkyCoord(ra=0, dec=1, unit="deg")

    footprint = polygon.ConvexSphericalPolygon([a, b, c, d])

    assert a in footprint
    assert b in footprint
    assert c in footprint
    assert d in footprint

    ab = SkyCoord(ra=0.5, dec=0, unit="deg")
    bc = SkyCoord(ra=1, dec=0.5, unit="deg")
    cd = SkyCoord(ra=0.5, dec=1, unit="deg")
    da = SkyCoord(ra=0, dec=0.5, unit="deg")

    assert ab in footprint
    assert bc in footprint
    assert cd in footprint
    assert da in footprint
