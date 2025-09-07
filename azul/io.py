# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azul
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
import numpy as np
import tifffile
from pathlib import Path

from azul import tile


def parse_slice(text: str):
    """
    Parse a 2D slice, e.g. ":,3:14".
    """
    parse_index = lambda i: int(i) if i else None
    return tuple(
        slice(*[parse_index(i) for i in axis.split(":")]) for axis in text.split(",")
    )


def read_fits(path: Path, slicing=None):
    """
    Read a region in the primary array of a FITS file.
    """
    data = fits.getdata(path)
    return data if slicing is None else data[slicing]


def write_tiff(rgb: np.ndarray, path: Path):
    """
    Write a normalized RGB image.
    """
    data = (rgb.flipud() * 65535).astype(np.uint16)
    tifffile.imwrite(path, data)


def read_channel(workdir: Path, channel: tile.Channel, slicing=None):
    """
    Read the region of one channel.
    """
    data = list(workdir.glob(f"EUC_*{channel}.fits"))  # FIXME
    rms = list(workdir.glob(f"EUC_*{channel}_FLAG.fits"))  # FIXME
    return tile.Channel(read_fits(data[0], slicing), read_fits(rms[0], slicing))


def read_iyjh(workdir: Path, slicing=None):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    return tile.Tile(
        read_channel(workdir, "VIS", slicing),
        read_channel(workdir, "NIR-Y", slicing),
        read_channel(workdir, "NIR-J", slicing),
        read_channel(workdir, "NIR-H", slicing),
    )
