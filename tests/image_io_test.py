# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero.image import io
from pathlib import Path


def test_standard_ext():

    assert io.standard_extension("/tmp/image.FTS") == ".fits"
    assert io.standard_extension("image.tif") == ".tiff"
    assert io.standard_extension("image.jpg") == ".jpeg"
    assert io.standard_extension("image.PNG") == ".png"
    assert io.standard_extension(".fits") == None


def test_product_metadata():

    assert "Software" in io.product_metadata(None)
    assert len(io.product_metadata(None)) == 1


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
