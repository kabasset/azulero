# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
from astropy.wcs import WCS
import cv2
import numpy as np
from pathlib import Path
import tifffile
import yaml

from azulero import _version
from azulero.tools.messaging import logger

# FIXME not in image.io

def parse_target(text: str):
    """
    Parse the workdir and slicing from a target string.
    """
    if text.endswith("]") and "[" in text:
        workdir, slicing = text.removesuffix("]").split("[")
        return Path(workdir), parse_slice(slicing)
    return Path(text), None


def parse_slice(text: str | None):
    """
    Parse a 2D slice from a string, e.g. ``:,3:14``.
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

# end FIXME


supported_formats = {
    ".fits": [".fits", ".fit", ".fts"],
    ".tiff": [".tiff", ".tif"],
    ".png": [".png"],
    ".jpeg": [".jpeg", ".jpg"],
    ".wcs": [".wcs"],
}


supported_wcs_formats = [".fits", ".tiff"]


def standard_extension(path: Path):
    """
    Get the standard supported extension of a path, if any, or ``None`` otherwise.
    """
    for e in supported_formats:
        if Path(path).suffix.lower() in supported_formats[e]:
            return e
    return None


# Reading


def find_wcs(workdir: Path, pattern: str):
    """
    Find a suitable file in some workdir to read WCS.
    """
    path = Path(pattern.format(channel="VIS")) # FIXME no hadcoded channel
    ext = standard_extension(path)
    if ext not in supported_wcs_formats:
        path = path.with_suffix(".wcs")
    return next(workdir.glob(path))


def read_wcs(path: Path, pattern: str):
    """
    Read a WCS.

    Files which do not support WCS must be accompanied by a file named after them with extension ``.wcs``.
    """
    ext = standard_extension(path)
    if ext == ".fits":
        with fits.open(path) as f:
            return WCS(f[0])
    elif ext == ".tiff":
        with tifffile.TiffFile(path) as f:
            return WCS(fits.Header(f.metadata)) # FIXME fix header, first?
    with open(path.with_suffix(".wcs")) as f:
        return WCS(yaml.safe_load(f))


def read_data(path: Path):
    """
    Read an image.
    """
    ext = standard_extension(path)
    if ext == ".fits":
        return fits.getdata(path)
    if ext == ".tiff":
        return tifffile.imread(path)
    return cv2.imread(path)


def read_product(path: Path, slicing: slice | None):
    """
    Read an image and WCS.
    """
    data = read_data(path)
    wcs = read_wcs(path)
    if slicing is None:
        return data, wcs
    if wcs is None:
        return data[slicing], None
    return data[slicing], wcs.slice(slicing)


def read_channel(workdir: Path, pattern: str, slicing=None):
    """
    Read the region of one channel.
    """
    data_files = list(workdir.glob(pattern))

    if len(data_files) == 1:
        return read_fits(data_files[0], slicing)

    logger.warning(f"{len(data_files)} files found with pattern: {pattern}")
    return _average([read_fits(f, slicing) for f in data_files])


def _average(slices: list):
    """
    Average arrays while discarding zeros.
    """
    stack = np.stack(slices)
    stack[stack == 0] = np.nan
    return np.nan_to_num(np.nanmedian(stack, axis=0))


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
    # FIXME get channel names from args


# Writing


def make_workdir(workspace, workdir):
    workdir = Path(workspace).expanduser() / workdir
    if workdir.is_dir():
        logger.warning(f"Working directory already exists: {workdir}")
    else:
        workdir.mkdir(parents=True)
    return workdir


def product_metadata(wcs: WCS | None):
    res = {} if wcs is None else dict(wcs.to_header())
    res["Software"] = f"{_version.__name_soft__} v{_version.__version__} (Antoine Basset, CNES)"
    return res


def write_product(path: Path, data: np.ndarray, wcs: WCS | None = None):
    """
    Write an image and optional WCS as an image file with WCS if supported,
    or as an image file and WCS files otherwise.
    """
    ext = standard_ext(path)
    if ext == ".fits":
        write_fits_product(path, data, wcs)
        metadata = product_metadata(wcs)
        fits.PrimaryHDU(data, header=metadata).writeto(path, overwrite=True)
        # FIXME get overwite policy from args
    elif ext == ".tiff":
        tifffile.imwrite(np.flipud(data), metadata=product_metadata(wcs))
    else:
        res = cv2.imwrite(path, np.flipud(data))
        # FIXME raise if not res
        write_wcs(path.with_suffix(".wcs"), wcs)


def write_wcs(wcs: WCS, path: Path):
    """
    Write a WCS object to a YAML file.
    """
    h = dict(wcs.to_header())
    with open(path, "w") as f:
        yaml.safe_dump(h, f)


def write_rgb(rgb: np.array, path: Path, norm_depth: int = None, wcs: WCS = None):
    """
    Write an RGB product.
    Optional ``norm_depth`` parameter is used to scale normalized images as either 8- or 16-bit integers.
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
        raise ValueError(f"Parameter ``norm_depth`` must be one of: None, 1, 8 or 16")
    
    ext = standard_ext(path)
    if ext == ".fits":
        channels = rgb.shape[2]
        write_fits_product(np.stack(rgb[:, :, i] for i in range(channels)), path, wcs)
    else:
        write_product(path, data[:, :, ::-1], wcs)


def write_mask(iyjh: np.ndarray, path: Path):
    """
    Write a 4-channel binary mask.
    """
    i, y, j, h = iyjh
    rgb = np.zeros((iyjh.shape[1], iyjh.shape[2], 3), dtype=np.uint8)
    rgb[:, :, 0] = i * 155 + h * 100
    rgb[:, :, 1] = i * 155 + j * 100
    rgb[:, :, 2] = i * 155 + y * 100
    write_rgb(rgb, path, norm_depth=1)
