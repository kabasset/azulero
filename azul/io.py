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


def read_channel(workdir: Path, channel: str, slicing=None):
    """
    Read the region of one channel.
    """
    data_files = list(workdir.glob(f"EUC_*{channel}_*.fits"))
    assert len(data_files) == 1
    data = read_fits(data_files[0], slicing)
    return data.view(np.ma.MaskedArray)  # FIXME

    # flag_files = list(workdir.glob(f"EUC_*{channel}-FLAG*.fits"))

    # if len(flag_files) == 0:
    #     print(f"WARNING: cannot find RMS map for channel {channel}")
    #     return data.view(np.ma.MaskedArray)

    # assert len(flag_files) == 1
    # mask = np.vectorize(
    #     tile.VisFlag.invalid if channel == "VIS" else tile.NirFlag.invalid
    # )
    # flagmap = read_fits(flag_files[0], slicing)
    # return np.ma.array(data, mask=mask(flagmap))


def read_iyjh(workdir: Path, slicing=None):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    return np.ma.stack(
        (
            read_channel(workdir, "VIS", slicing),
            read_channel(workdir, "NIR-Y", slicing),
            read_channel(workdir, "NIR-J", slicing),
            read_channel(workdir, "NIR-H", slicing),
        )
    )
