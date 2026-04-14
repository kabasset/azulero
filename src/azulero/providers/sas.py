# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle, SkyCoord
from astroquery.esa.euclid import EuclidClass
import contextlib  # intercept astroquery prints
from dataclasses import dataclass
from io import StringIO
import netrc


@dataclass(frozen=True)
class Tile(object):
    index: str
    mode: str
    dsr: str
    distance: float

    def __str__(self) -> str:
        return f"{self.mode}: {self.index} ({self.dsr}); distance: {self.distance:.2f}°"


def tile(res, target):
    center = SkyCoord(res["ra"], res["dec"], unit="deg", frame="icrs")
    distance = center.separation(target).value
    return Tile(
        str(res["tile_index"]),
        res.get("processing_mode", "UNKNOWN"),
        res.get("data_set_release", "UNKNOWN"),
        distance,
    )


class SAS:

    def __init__(self, env):

        self.env = env
        self.euclid = EuclidClass(environment=env)

        # Intercept stderr, stdout
        err, out = StringIO(), StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            auth = netrc.netrc().authenticators("easidr.esac.esa.int")
            self.euclid.login(user=auth[0], password=auth[2])
        if err.getvalue():
            raise RuntimeError(err.getvalue())

    def __del__(self):
        err, out = StringIO(), StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            self.euclid.logout()
        if err.getvalue():
            raise RuntimeError(err.getvalue())

    def query_tiles(self, radec: SkyCoord, dsrs: list[str]):
        dsrs_text = ",".join("'" + d + "'" for d in dsrs)
        select_text = "tile_index,ra,dec,data_set_release"
        if self.env != "PDR":
            select_text += ",processing_mode"
        q = f"SELECT {select_text} FROM sedm.mosaic_product WHERE (mosaic_product.data_set_release IN ({dsrs_text})) AND INTERSECTS(CIRCLE({radec.ra.value},{radec.dec.value},0),fov)=1"
        res = self.euclid.launch_job(q).get_results()
        return sorted(
            sorted(
                set(tile(r, radec) for r in res),
                key=lambda t: t.distance,
            ),
            key=lambda t: t.mode,
        )  # FIXME sorting to retrieve.py to be applied to all providers

    def query_datafiles(self, tile: str, dsr: str):
        products = self.euclid.get_product_list(
            tile_index=tile, product_type="DpdMerBksMosaic"
        )
        return {
            str(p["file_name"]): str(p["filter_name"])
            for p in products
            if str(p["release_name"]) == dsr
        }

    def download_datafile(
        self, name: str, path: Path, target=None, radius: Angle = None
    ):
        if radius is None:
            path = self.euclid.get_product(file_name=name, output_file=path)
        else:
            q = f"SELECT file_path, instrument_name FROM sedm.mosaic_product WHERE file_name='{name}'"
            res = self.euclid.launch_job(q).get_results()[0]
            path = self.euclid.get_cutout(
                file_path=Path(res["file_path"]) / name,
                instrument=res["instrument_name"],
                id=target.index,
                coordinate=target.coord,
                radius=radius,
                output_file=path,
            )
