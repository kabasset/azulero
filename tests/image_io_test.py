# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.wcs import WCS
import numpy as np
from pathlib import Path
import tempfile

from azulero.image import io


def test_standard_ext():

    assert io.standard_extension("/tmp/image.FTS") == ".fits"
    assert io.standard_extension("image.tif") == ".tiff"
    assert io.standard_extension("image.jpg") == ".jpeg"
    assert io.standard_extension("image.PNG") == ".png"
    assert io.standard_extension(".fits") == None


def test_product_metadata():

    assert "SOFTWARE" in io.product_metadata(None)
    assert "AUTHOR" in io.product_metadata(None)
    assert "WCSAXES" not in io.product_metadata(None)
    assert "SOFTWARE" in io.product_metadata(WCS())
    assert "AUTHOR" in io.product_metadata(WCS())
    assert "WCSAXES" in io.product_metadata(WCS())


def test_data_io():
    filenames = ["data.FTS", "data.TIF", "data.PNG"]
    # We don't test JPG as it is compressed
    w = 16
    h = 9
    d = 3
    r = np.arange(w * h, dtype=np.uint8).reshape(h, w)
    g = r // 2
    b = g // 2
    data = np.stack((b, g, r), axis=-1)
    wcs = WCS()
    wcs.array_shape = (h, w)
    check_data_io("data.fits", r, None)
    check_data_io("data.FTS", r, wcs)
    check_data_io("data.tiff", data, None)
    check_data_io("data.TIF", data, wcs)
    check_data_io("data.png", data, None)
    check_data_io("data.PNG", data, wcs)


def check_data_io(filename, data, wcs):
    with tempfile.TemporaryDirectory() as workdir:
        filename = Path(workdir) / filename
        res = io.write_product(filename, data, wcs)
        assert res
        print(res)
        res = io.read_product(filename)
        assert res[0] is not None
        assert np.array_equal(res[0].shape, data.shape)
        assert np.array_equal(res[0], data)
        if wcs is None:
            assert res[1] is None
        else:
            assert res[1] is not None
            assert res[1].to_header_string() == wcs.to_header_string()
