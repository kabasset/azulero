# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle, SkyCoord
from astropy.table import Table
from astroquery.esa.euclid import EuclidClass
import contextlib  # intercept astroquery prints
from dataclasses import dataclass
from io import StringIO

from azulero.providers.tiling import Tile, Target
from azulero.tools.secret import Auth


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

    def __init__(self, env: str, user: str | None):

        self.env = env
        self.__euclid = EuclidClass(environment=env)

        if self.env != "PDR":  # The only environment without authentication
            self._authenticate(user)

    def _authenticate(self, user: str | None):
        auth = Auth("easidr.esac.esa.int", user)
        # Intercept stderr, stdout
        err, out = StringIO(), StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            self.__euclid.login(user=auth.user, password=auth.password.value)
        if err.getvalue():
            raise RuntimeError(err.getvalue())

    def __del__(self):
        err, out = StringIO(), StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            self.__euclid.logout()
        if err.getvalue():
            raise RuntimeError(err.getvalue())

    def get_table(self, query: str) -> Table:
        res = self.__euclid.launch_job(query).get_results()  # type: ignore
        if not isinstance(res, Table):
            raise RuntimeError(f"The query returned an object of type: {type(res)}")
        return res

    def query_tile_attributes(self, index: str) -> list[Tile]:
        return [Tile(index)]  # FIXME mode, dsrs

    def query_radec_tiles(self, radec: SkyCoord, dsrs: list[str]) -> list[Tile]:
        dsrs_text = ",".join("'" + d + "'" for d in dsrs)
        select_text = "tile_index,ra,dec,data_set_release"
        if self.env != "PDR":
            select_text += ",processing_mode"
        q = f"SELECT {select_text} FROM sedm.mosaic_product WHERE (mosaic_product.data_set_release IN ({dsrs_text})) AND INTERSECTS(CIRCLE({radec.ra.value},{radec.dec.value},0),fov)=1"
        res = self.get_table(q)
        return [tile(r, radec) for r in res]

    def query_tile_datafiles(self, tile: Tile) -> dict[str, str]:
        products = self.__euclid.get_product_list(
            tile_index=tile.index, product_type="DpdMerBksMosaic"
        )
        assert products is not None  # FIXME raise
        return {
            str(p["file_name"]): str(p["filter_name"])
            for p in products
            if str(p["release_name"]) == tile.dsr
        }

    def download_datafile(self, name: str, path: Path):
        self.__euclid.get_product(file_name=name, output_file=path)

    def download_cutout(self, name: str, path: Path, target: Target):
        q = f"SELECT file_path, instrument_name FROM sedm.mosaic_product WHERE file_name='{name}'"
        res = self.get_table(q)[0]
        self.__euclid.get_cutout(
            file_path=Path(res["file_path"]) / name,  # type: ignore
            instrument=res["instrument_name"],
            id=target.tile.index,
            coordinate=target.coord,
            radius=target.radius,
            output_file=path,
        )  # type: ignore
