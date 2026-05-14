# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from astropy.coordinates import Angle, SkyCoord
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.wcs import WCS

from azulero.tools.messaging import logger
from azulero.providers import tiling


class LocalCutout:
    """
    Decorator class which adds local cutout service to a data provider without a cutout service.
    The datafiles are downloaded in full in the tile folder,
    and cutouts are extracted from them and written to the workdir.
    """

    def __init__(self, provider):
        self.provider = provider

    def download_datafile(self, name: str, path: Path) -> Path:
        if (path).exists():
            logger.bullet(f"Tile file already exists; Skip: {name}")
            return path
        return self.provider.download_datafile(name, path)

    def download_cutout(
        self,
        name: str,
        path: Path,
        target: tiling.Target,
        radius: Angle,
    ) -> Path:
        tiledir = path.parent.parent / path.name  # FIXME resolve tile folder
        logger.warning(
            f"Cutout retrieval is not supported by this provider. "
            f"Cutting locally a full tile to be retrieved in: {tiledir}"
        )
        tile = self.download_datafile(name, tiledir)
        return self._cut(tile, path, target.coord, radius)

    def _cut(self, input: Path, output: Path, coord: SkyCoord, radius: Angle) -> Path:
        with fits.open(input) as f:
            hdu = f[0]
            wcs = WCS(hdu.header)
            cutout = Cutout2D(hdu.data, position=coord, size=2 * radius, wcs=wcs)
            hdu.data = cutout.data
            hdu.header.update(cutout.wcs.to_header())
            hdu.writeto(output, overwrite=True)  # FIXME overwrite policy from args
        return output
