# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from azulero import mask


def test_flagging():

    assert mask.VisFlag.valid(0)
    assert mask.VisFlag.invalid(1)
    assert mask.VisFlag.invalid(2)
    assert mask.VisFlag.invalid(3)
    assert mask.VisFlag.invalid(4)
    assert mask.VisFlag.valid(8)

    assert mask.NirFlag.valid(0)
    assert mask.NirFlag.valid(1)
    assert mask.NirFlag.invalid(2)
    assert mask.NirFlag.invalid(3)
    assert mask.NirFlag.invalid(4)
    assert mask.NirFlag.invalid(8)
    assert mask.NirFlag.valid(16)
    assert mask.NirFlag.invalid(2**6)
    assert mask.NirFlag.invalid(2**7)
    assert mask.NirFlag.invalid(2**9)
    assert mask.NirFlag.invalid(2**10)
    assert mask.NirFlag.valid(2**11)
    assert mask.NirFlag.invalid(2**12)


def test_inpainting():

    data = np.ones((9, 16, 3))
    flags = np.zeros((9, 16))
    data[1, 1, 1] = 0
    flags[1, 1] = 1

    res = mask.inpaint(data, flags)

    assert np.all(res == 1)
