# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
import cv2
import numpy as np
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


def write_rgb(rgb: np.array, path: Path, norm_depth: int = None):
    """
    Write an RGB image.
    Optional `norm_depth` parameter is used to scale normalized images as either 8- or 16-bit integers.
    By default, for TIFF files, image is scaled by 65563 and for other files, by 255.
    Setting it to 1 won't apply any normalization.
    """
    if norm_depth is None:
        norm_depth = 16 if path.suffix.lower() in (".tif", ".tiff") else 8
    if norm_depth == 1:
        data = rgb
    elif norm_depth == 8:
        data = np.round(rgb * 255).astype(np.uint8)
    elif norm_depth == 16:
        data = np.round(rgb * 65535).astype(np.uint16)
    else:
        raise ValueError(f"Parameter `norm_depth` must be one of: None, 1, 8 or 16")
    cv2.imwrite(path, np.flipud(data)[:, :, ::-1])


def write_mask(iyjh: np.ndarray, path: Path):
    """
    Write a 4-channel binary mask.
    """
    i, y, j, h = iyjh
    rgb = np.zeros((iyjh.shape[1], iyjh.shape[2], 3), dtype=np.uint8)
    rgb[:, :, 0] = i * 155 + h * 100
    rgb[:, :, 1] = i * 155 + j * 100
    rgb[:, :, 2] = i * 155 + y * 100
    write_rgb(rgb, path, 1)


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
