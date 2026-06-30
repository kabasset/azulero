# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from pathlib import Path

from azulero.tools import parsing


def test_1D_slice_parsing():

    text = "50:70"
    slicing = parsing.parse_slice(text)
    assert slicing == slice(50, 70)


def test_2D_slice_parsing():

    text = ":,3:14"
    slicing = parsing.parse_slice(text)
    assert slicing == (slice(None, None), slice(3, 14))
    a = np.zeros((9, 16))
    b = a[slicing]
    assert b.shape == (9, 11)


def test_target_parsing():

    t, s = parsing.parse_target("tile")
    assert t == Path("tile")
    assert s is None

    t, s = parsing.parse_target("workdir[:,:]")
    assert t == Path("workdir")
    assert s == (slice(None, None), slice(None, None))


def test_rendering():

    tiledir = Path("102159776")
    workdir = tiledir / "UGC11116"
    template = "{workdir}/{1|Tile}_{0}_{step}_{-1}.tiff"

    assert (
        parsing.render_template(template, *workdir.parts, workdir=workdir)
        == "102159776/UGC11116/UGC11116_102159776_{step}_UGC11116.tiff"
    )
    assert (
        parsing.render_template(template, *tiledir.parts, workdir=tiledir)
        == "102159776/Tile_102159776_{step}_102159776.tiff"
    )
    assert parsing.render_template(template, workdir="") == "/Tile_{0}_{step}_{-1}.tiff"
