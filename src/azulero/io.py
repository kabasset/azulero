# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
import numpy as np
import tifffile
from pathlib import Path


def parse_tile(text: str):
    tile_slicing = text.split("[")
    if len(tile_slicing) == 1:
        return tile_slicing[0], None
    return tile_slicing[0], parse_slice(tile_slicing[1][:-1])


def parse_slice(text: str):
    """
    Parse a 2D slice, e.g. ":,3:14".
    """
    if text is None:
        return None
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
    data = np.flipud(rgb * 65535).astype(np.uint16)
    tifffile.imwrite(path, data)


def read_channel(workdir: Path, channel: str, slicing=None):
    """
    Read the region of one channel.
    """
    data_files = list(workdir.glob(f"EUC_*{channel}_*.fits"))
    assert len(data_files) == 1
    return read_fits(data_files[0], slicing)


def read_iyjh(workdir: Path, slicing=None):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    return np.stack(
        (
            read_channel(workdir, "VIS", slicing),
            read_channel(workdir, "NIR-Y", slicing),
            read_channel(workdir, "NIR-J", slicing),
            read_channel(workdir, "NIR-H", slicing),
        )
    )
