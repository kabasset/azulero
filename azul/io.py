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


def read_channel(workdir: Path, channel: tile.Channel, slicing=None):
    """
    Read the region of one channel.
    """
    data_files = list(workdir.glob(f"EUC_*{channel}_*.fits"))
    assert len(data_files) == 1
    data = read_fits(data_files[0], slicing)

    rms_files = list(workdir.glob(f"EUC_*{channel}-FLAG*.fits"))
    if len(rms_files) == 0:
        print(f"WARNING: cannot find RMS map for channel {channel}")
        rms = np.zeros_like(data, dtype=np.int8)
    else:
        assert len(rms_files) == 1
        rms = read_fits(rms_files[0], slicing)
    return tile.Channel(data, rms)


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
