# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle, SkyCoord
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.wcs import WCS

from azulero.tools.messaging import logger
from azulero.providers import tiling, protocol


class LocalCutout:
    """
    Decorator class which adds local cutout service to a data provider without a cutout service.
    The datafiles are downloaded in full in the tile folder,
    and cutouts are extracted from them and written to the workdir.
    """

    def __init__(self, provider: protocol.DataStore):
        self.provider = provider

    def download_datafile(self, name: str, path: Path):
        if (path).exists():
            logger.bullet(f"Tile file already exists; Skip: {name}")
        else:
            self.provider.download_datafile(name, path)

    def download_cutout(self, name: str, path: Path, target: tiling.Target):
        tiledir = path.parent.parent  # FIXME resolve tile folder
        logger.warning(
            f"Cutout retrieval is not supported by this provider. "
            f"Cutting locally a full tile to be retrieved in: {tiledir}"
        )
        self.download_datafile(name, tiledir / path.name)
        assert target.coord is not None and target.radius is not None
        local_cutout(tiledir / path.name, path, target.coord, target.radius)


def local_cutout(input: Path, output: Path, coord: SkyCoord, radius: Angle):
    with fits.open(input) as f:
        hdu: fits.ImageHDU = f[0]  # type: ignore
        wcs = WCS(hdu.header)
        cutout = Cutout2D(hdu.data, position=coord, size=2 * radius, wcs=wcs)
        hdu.data = cutout.data
        assert cutout.wcs is not None
        hdu.header.update(cutout.wcs.to_header())
        hdu.writeto(output, overwrite=True)  # FIXME overwrite policy from args
