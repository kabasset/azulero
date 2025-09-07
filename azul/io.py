# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
import glob
import numpy as np
import tifffile

from azul import tile


def parse_slice(text):
    """
    Parse a 2D slice, e.g. ":,3:14".
    """
    parse_index = lambda i: int(i) if i else None
    return tuple(
        slice(*[parse_index(i) for i in axis.split(":")]) for axis in text.split(",")
    )


def read_fits(path, slicing=None):
    """
    Read a region in the primary array of a FITS file.
    """
    data = fits.getdata(path)
    return data if slicing is None else data[slicing]


def write_tiff(rgb: np.ndarray, path):
    """
    Write a normalized RGB image.
    """
    data = (rgb.flipud() * 65535).astype(np.uint16)
    tifffile.imwrite(path, data)


def read_channel(dir, channel, slicing=None):
    """
    Read the region of one channel.
    """
    data = glob.glob(dir / f"EUC_*{channel}*.fits")
    rms = glob.glob(dir / f"EUC_*{channel}*.fits")  # FIXME
    assert len(data) == 1
    assert len(rms) == 1
    return tile.Channel(read_fits(data[0], slicing), read_fits(rms[0], slicing))


def read_iyjh(dir, slicing=None):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    return tile.Tile(
        read_channel(dir, "VIS", slicing),
        read_channel(dir, "NIR-Y", slicing),
        read_channel(dir, "NIR-J", slicing),
        read_channel(dir, "NIR-H", slicing),
    )
