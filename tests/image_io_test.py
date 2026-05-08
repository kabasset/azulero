# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.wcs import WCS
import numpy as np
from pathlib import Path

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


def test_slice_parsing():

    text = ":,3:14"
    slicing = io.parse_slice(text)
    assert slicing == (slice(None, None), slice(3, 14))
    a = np.zeros((9, 16))
    b = a[slicing]
    assert b.shape == (9, 11)


def test_target_parsing():

    t, s = io.parse_target("tile")
    assert t == Path("tile")
    assert s is None

    t, s = io.parse_target("workdir[:,:]")
    assert t == Path("workdir")
    assert s == (slice(None, None), slice(None, None))


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
    workdir = Path("/tmp")  # FIXME temporary dir
    io.write_product(workdir / filename, data, wcs)
    res = io.read_product(workdir / filename)
    assert res[0] is not None
    assert np.array_equal(res[0].shape, data.shape)
    assert np.array_equal(res[0], data)
    if wcs is None:
        assert res[1] is None
    else:
        assert res[1].to_header_string() == wcs.to_header_string()
