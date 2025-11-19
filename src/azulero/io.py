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


def parse_map(text: str, dtype=float):
    """
    Parse a comma-separated list of 'key:value' pairs.
    """
    if not text:
        return []
    pairs = [p.split(":") for p in text.split(",")]
    return [[dtype(x), dtype(y)] for x, y in pairs]


def read_fits(path: Path, slicing=None):
    """
    Read a region in the primary array of a FITS file.
    """
    data = fits.getdata(path)
    return data if slicing is None else data[slicing]


def make_workdir(workspace, tile):
    workdir = Path(workspace).expanduser() / tile
    if workdir.is_dir():
        print("WARNING: Working directory already exists.")
    else:
        workdir.mkdir(parents=True)
    return workdir


def write_fits(data: np.array, path: Path):
    """
    Write an SIF file.
    """
    fits.PrimaryHDU(data).writeto(path, overwrite=True)


def write_tiff(rgb: np.ndarray, path: Path):
    """
    Write a normalized RGB image.
    """
    data = np.flipud(rgb * 65535).astype(np.uint16)
    tifffile.imwrite(path, data)


def write_mask(iyjh: np.ndarray, path: Path):
    """
    Write a 4-channel binary mask.
    """
    i, y, j, h = iyjh
    rgb = np.zeros((iyjh.shape[1], iyjh.shape[2], 3), dtype=np.uint8)
    rgb[:, :, 0] = i * 155 + h * 100
    rgb[:, :, 1] = i * 155 + j * 100
    rgb[:, :, 2] = i * 155 + y * 100
    tifffile.imwrite(path, np.flipud(rgb))


def read_channel(workdir: Path, pattern: str, slicing=None):
    """
    Read the region of one channel.
    """
    data_files = list(workdir.glob(pattern))

    if len(data_files) == 1:
        return read_fits(data_files[0], slicing)

    print(f"WARNING: {len(data_files)} files found with pattern: {pattern}")
    return _average([read_fits(f, slicing) for f in data_files])


def _average(slices: list):
    """
    Average arrays, discarding zeros.
    """
    stack = np.stack(slices)
    # FIXME replace 0 with np.nan
    return np.nan_to_num(
        np.nanmean(stack, axis=0, where=(stack != 0)), copy=False
    )  # FIXME nanmedian


def read_iyjh(workdir: Path, slicing=None, template="{}"):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    return np.stack(
        (
            read_channel(workdir, template.format(channel="VIS"), slicing),
            read_channel(workdir, template.format(channel="NIR-Y"), slicing),
            read_channel(workdir, template.format(channel="NIR-J"), slicing),
            read_channel(workdir, template.format(channel="NIR-H"), slicing),
        )
    )
