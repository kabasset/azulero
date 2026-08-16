# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.wcs import WCS
from astropy.coordinates import Angle, SkyCoord
import numpy as np
from pathlib import Path

from azulero import retrieve, process
from azulero.image import color
from azulero.providers.tiling import Target


class DataProvider:
    """
    Data provider.

    Args:
        name: The data provider name.
        user: The data provider user name (optional if the netrc file was set up).
        data_store: The data store name (use ``"labs"`` in ESA Datalabs).
        tiling_file: The tiling Geojson file, for optimization purpose.
    """

    def __init__(
        self,
        name: str,
        user: str | None = None,
        data_store: str | None = None,
        tiling_file: Path | None = None,
    ):
        self.provider = retrieve.DataProvider(name, user, data_store, tiling_file)

    def query_coord_tiles(
        self,
        coord: SkyCoord,
        dsrs: list[str],
        modes: list[str],
    ) -> list[str]:
        """
        Query the list of tiles which contain a given coordinate.

        Args:
            coord: The target coordinate.
            dsrs: The ordered list of dataset releases.
            modes: The ordered list of processing modes.

        Returns:
            The list of tile indices.
        """
        targets = self.provider.query_radec_tiles("", coord, None, dsrs, modes)
        return [t.tile for t in targets]

    def query_tile_datafiles(self, index: str, dsr: str) -> list[str]:
        """
        Query the datafiles of a tile.

        Args:
            index: The tile index.
            dsr: The Dataset Release name.

        Returns:
            The list of file names.
        """
        return [f for f in self.provider.query_tile_datafiles(index, dsr)]

    def download_datafiles(
        self,
        datafiles: list[str],
        workdir: Path,
        overwrite: bool = False,
    ):
        """
        Download datafiles of an entire tile.

        Args:
            datafiles: The list of datafile names.
            workdir: The destination directory.
            overwrite: Boolean flag to enable or disable overwriting.
        """
        self.provider.download_datafiles(datafiles, workdir, Target(), overwrite)

    def download_cutouts(
        self,
        datafiles: list[str],
        workdir: Path,
        center: SkyCoord,
        radius: Angle,
        overwrite: bool = False,
    ):
        """
        Download cutouts.

        Args:
            datafiles: The list of datafile names.
            workdir: The destination directory (will be created if missing).
            center: The cutout center.
            radius: The cutout radius.
            overwrite: Boolean flag to enable or disable overwriting.
        """
        self.provider.download_datafiles(
            datafiles, workdir, Target("", "", center, radius), overwrite
        )


Transform = color.Transform
"""
Transformation parameters.

Args:
    iyjh_zero_points: Zero points of each channel.
    iyjh_scaling: Scaling of each channel (for white balance).
    iyjh_fwhm: PSF full width at half-maximum of each channel.
    sharpen_strength: Unsharp masking strength.
    nir_to_l: NIR-to-L rate.
    i_to_b: I-to-B rate.
    y_to_g: Y-to-G rate.
    j_to_r: J-to-R rate.
    hue: Hue rotation angle in degrees.
    saturation: Saturation gain.
    stretch: Stretching parameter.
    neg_overshoot: Negative overshooting parameter.
    bw: Black and white points in AB-mag.
    bgr_curves: Curve adjustment knots for each channel.
"""


def process_iyjh(
    iyjh: np.ndarray,
    wcs: WCS | None = None,
    transform: Transform = Transform(),
    output: str = "",
) -> np.ndarray:
    """
    Process an image according to transformation parameters,
    optionally save the rendered color image.

    Args:
        iyjh:
            A stack of the I, Y, J, H arrays (e.g. ``iyjh[1]`` is the NIR-Y channel).
        wcs:
            The WCS parameters or ``None``.
        transform:
            The transformation parameters.
        output:
            The output file name.
            An empty string disables writing.

    Returns:
        A normalized BGR image (OpenCV layout).
    """
    bgr = process.process_iyjh(np.astype(iyjh, np.float32), wcs, transform, output)
    return np.flipud(bgr)
