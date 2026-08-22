# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.io import fits
from astropy.wcs import WCS
import cv2
import json
import numpy as np
from pathlib import Path
import tifffile
import yaml

from azulero import _version
from azulero.tools.messaging import logger

supported_formats: dict[str, list[str]] = {
    ".fits": [".fits", ".fit", ".fts"],
    ".tiff": [".tiff", ".tif"],
    ".png": [".png"],
    ".jpeg": [".jpeg", ".jpg"],
}


supported_wcs_formats: list[str] = [".fits", ".tiff"]


def standard_extension(path: str | Path) -> str | None:
    """
    Get the standard supported extension of a path, if any, or ``None`` otherwise.
    """
    for e in supported_formats:
        if Path(path).suffix.lower() in supported_formats[e]:
            return e
    return None


# Reading


def find_wcs(workdir: Path, pattern: str) -> Path | None:
    """
    Find a suitable file in some workdir to read WCS, or ``None``.
    """
    path = Path(pattern.format(channel="VIS"))  # FIXME no hardcoded channel
    ext = standard_extension(path)
    if ext not in supported_wcs_formats:
        path = path.with_suffix(".wcs")
    return next(workdir.glob(str(path)), None)


def has_wcs(metadata: dict | fits.Header) -> bool:
    """
    Detect WCS keywords.
    """
    keywords = ["WCSAXES", "CRVAL1", "CRPIX1", "CDELT1", "CTYPE1"]
    for k in keywords:
        if k in metadata:
            return True
    return False


def read_wcs(path: Path, slicing: tuple | None = None) -> WCS | None:
    """
    Read a WCS.

    For TIFF files, ``ImageDescription`` metadata in the first page are used.
    Files which do not support WCS must be accompanied by a file named after them with extension ``.wcs``.
    If no WCS is found, then ``None is returned``.
    """
    ext = standard_extension(path)
    if ext == ".fits":
        with fits.open(path) as f:
            h = f[0].header  # type: ignore
        if not has_wcs(h):
            return None
        wcs = WCS(h)
    elif ext == ".tiff":
        with tifffile.TiffFile(path) as f:
            desc = f.pages[0].tags["ImageDescription"].value  # type: ignore
        metadata = json.loads(desc)
        if not has_wcs(metadata):
            return None
        h = {k: v for k, v in metadata.items() if not isinstance(v, list)}
        wcs = WCS(h)
    else:
        wcs_path = path.with_suffix(".wcs")
        if not wcs_path.exists():
            return None
        with open(wcs_path) as f:
            wcs = WCS(yaml.safe_load(f))
    return wcs if slicing is None else wcs.slice(slicing)


def read_data(path: Path, slicing: tuple | None = None) -> np.ndarray | None:
    """
    Read an image.

    FITS supports only grayscale images.
    Color images are loaded with shape ``(height, width, depth)``
    and color channels are ordered as ``(blue, green, red)``.
    """
    ext = standard_extension(path)
    if ext == ".fits":
        with fits.open(path) as f:
            p: fits.PrimaryHDU = f[0]  # type: ignore
            data = p.data
    else:
        data = cv2.imread(path)
        if data is not None:
            data = np.flipud(data)
    return data if (data is None or slicing is None) else data[slicing]


def read_product(
    path: Path, slicing: tuple | None = None
) -> tuple[np.ndarray | None, WCS | None]:
    """
    Read an image and WCS.
    """
    data = read_data(path, slicing)
    wcs = read_wcs(path, slicing)
    return data, wcs


def read_channel(workdir: Path, pattern: str, slicing=None) -> np.ndarray:
    """
    Read the region of one channel.
    """
    files = list(workdir.glob(pattern))
    if len(files) == 0:
        raise RuntimeError(f"No file found with pattern: {pattern}")

    if len(files) == 1:
        data = read_data(files[0], slicing)
        if data is None:
            raise RuntimeError(f"Cannot read file: {files[0]}")
        return data

    logger.warning(f"{len(files)} files found with pattern: {pattern}")
    return _average([read_data(f, slicing) for f in files])


def _average(slices: list):
    """
    Average arrays while discarding zeros.
    """
    valid_slices = [s for s in slices if s is not None]
    if len(valid_slices) < len(slices):
        logger.warning(
            f"Invalid input(s) discarded: {len(slices) - len(valid_slices)}/{len(slices)}"
        )
    stack = np.stack(valid_slices)
    stack[stack == 0] = np.nan
    return np.nan_to_num(np.nanmedian(stack, axis=0))


def read_iyjh(
    workdir: Path,
    slicing: tuple | None = None,
    template: str = "*{channel}*.fits",
    channels: list[str] = ["VIS", "NIR-Y", "NIR-J", "NIR-H"],
):
    """
    Read the region of a VIS- and NIR-covered tile.
    """
    if workdir.is_file():
        return np.stack([read_ext(workdir, c, slicing) for c in channels])
    return np.stack(
        [read_channel(workdir, template.format(channel=c), slicing) for c in channels]
    )


def read_ext(filename: Path, ext: str, slicing=None) -> np.ndarray:
    """
    Read the region of one FITS extension.
    """
    with fits.open(filename) as f:
        data = f[ext].data  # type: ignore
        if slicing is not None:
            return data[slicing]
        return data


# Writing


def make_workdir(workdir: Path) -> Path:
    if workdir.is_dir():
        logger.warning(f"Working directory already exists: {workdir}")
    else:
        workdir.mkdir(parents=True)
    return workdir


def product_header(wcs: WCS | None = None) -> fits.Header:
    h = fits.Header() if wcs is None else wcs.to_header()
    h["SOFTWARE"] = f"{_version.__name_soft__} v{_version.__version__}"
    h["AUTHOR"] = "Antoine Basset"
    return h


def product_metadata(wcs: WCS | None = None) -> dict:
    return dict(product_header(wcs))


def write_product(path: Path, data: np.ndarray, wcs: WCS | None = None) -> Path | None:
    """
    Write an image and optional WCS as an image file with WCS if supported,
    or as an image file and WCS files otherwise.

    If the path is not a file, return it early.
    """
    if not path.suffix:
        return path

    ext = standard_extension(path)
    if ext == ".fits":
        fits.PrimaryHDU(data, header=product_header(wcs)).writeto(path, overwrite=True)
        # FIXME get overwrite policy from args
        res = True  # FIXME False if fits.verify.VerifyError raised
    elif ext == ".tiff":
        if data.ndim == 3:
            data = data[:, :, ::-1]
            # FIXME what about alpha? use cv2.RGBA2BGRA and the likes
        tifffile.imwrite(path, np.flipud(data), metadata=product_metadata(wcs))
        res = True  # FIXME
    else:
        res = cv2.imwrite(path, np.flipud(data))
        if wcs is not None:
            write_wcs(path.with_suffix(".wcs"), wcs)
    return path if res else None


def write_wcs(path: Path, wcs: WCS):
    """
    Write a WCS object to a YAML file.
    """
    h = dict(wcs.to_header())
    with open(path, "w") as f:
        yaml.safe_dump(h, f)


def write_rgb(
    rgb: np.ndarray, path: Path, norm_depth: int | None = None, wcs: WCS | None = None
) -> Path | None:
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

    return write_product(path, data[:, :, ::-1], wcs)


def write_normalized_bgr(
    path: Path, bgr: np.ndarray, wcs: WCS | None, bits=0
) -> Path | None:
    if bits == 0:
        bits = 16 if standard_extension(path) == ".tiff" else 8
    if bits == 1:
        data = bgr
    elif bits == 8:
        data = np.round(bgr * 255).astype(np.uint8)
    elif bits == 16:
        data = np.round(bgr * 65535).astype(np.uint16)
    else:
        raise ValueError(f"Parameter ``bits`` must be one of: 0, 1, 8 or 16")
    return write_product(path, data, wcs)


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
