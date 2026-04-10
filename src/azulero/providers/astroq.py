# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astroquery.esa.euclid import Euclid, EuclidClass
import contextlib  # intercept astroquery prints
from io import StringIO
import netrc


class AstroQuery:

    def __init__(self, env="IDR"):
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

    def query_datafiles(self, tile, dsr):
        products = self.euclid.get_product_list(
            tile_index=tile, product_type="DpdMerBksMosaic"
        )
        return {
            str(p["file_name"]): str(p["filter_name"])
            for p in products
            if str(p["release_name"]) == dsr
        }

    def download_datafile(self, name, path):
        path = self.euclid.get_product(file_name=name, output_file=path)
