# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from astropy.io import fits
from astroquery.simbad import Simbad
import requests
import sys


def object_radec(name: str):
    res = Simbad().query_object(name)
    assert len(res) > 0, f"Object not found: {name}"
    assert len(res) < 2, f"Several objects found: {name}"
    return float(res[0]["ra"]), float(res[0]["dec"])


def radec_tiles(radec: tuple):
    epsilon = 1e-8  # FIXME param?
    query = {
        "project": "EUCLID",
        "class_name": "DpdMerBksMosaic",
        "spatial_query": f"INTERSECT(0.01,101) BOUNDINGBOX({radec[0]-epsilon} {radec[1]-epsilon}, {radec[0]+epsilon} {radec[1]+epsilon})",
        "fields": "Header.ProductId",  # "Data.TileIndex:Data.RaCen:Data.DecCen",
    }
    lines = (
        requests.get("https://eas-dps-rest-ops.esac.esa.int/REST", params=query)
        .text.replace('"', "")
        .split()
    )
    print("\n".join(lines))
    tiles = {}
    for l in lines[1:]:
        index, ra, dec = l.split(",")
        tiles[index] = (ra, dec)
    return tiles


def object_tiles(name: str):
    return radec_tiles(object_radec(name))


@dataclass
class TileBox(object):
    ra_center: float
    dec_center: float
    ra_radius: float
    dec_radius: float

    def __contains__(self, radec: tuple):
        ra, dec = radec
        return (
            ra > self.ra_min()
            and ra < self.ra_max()
            and dec > self.dec_min()
            and dec < self.dec_max()
        )
        # FIXME bounds

    def ra_min(self):
        return self.ra_center - self.ra_radius

    def ra_max(self):
        return self.ra_center + self.ra_radius

    def dec_min(self):
        return self.dec_center - self.dec_radius

    def dec_max(self):
        return self.dec_center + self.dec_radius

    def __repr__(self):
        return f"[{self.ra_min()}:{self.ra_max()}, {self.dec_min()}:{self.dec_max()}]"


class Tiling(object):

    def __init__(self, filename):
        data = self._first_bintable(filename)
        indices = data["tileId"]
        ra_centers = data["RA"]
        dec_centers = data["Dec"]
        widths = data["width"]
        heights = data["height"]
        self.tiles = {
            t[0]: TileBox(t[1], t[2], t[3] / 120, t[4] / 120)
            for t in zip(indices, ra_centers, dec_centers, widths, heights)
        }

    def _first_bintable(self, filename):
        with fits.open(filename) as f:
            for hdu in f:
                if isinstance(hdu, fits.BinTableHDU):
                    return hdu.data

    def __call__(self, radec: tuple):
        return {t: self.tiles[t] for t in self.tiles if radec in self.tiles[t]}


if __name__ == "__main__":
    tiling = Tiling("~/Downloads/field_all_sky_overview.fits")
    for arg in sys.argv[1:]:
        radec = object_radec(arg)
        print(f"{arg}: {radec}")
        tiles = tiling(radec)
        if len(tiles) == 0:
            print("- WARNING: No tile found.")
        for t in tiles:
            print(f"- {t}: {tiles[t]}")
