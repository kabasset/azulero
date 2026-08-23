# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
from pathlib import Path
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy import wcs
import cv2
from dataclasses import dataclass
import numpy as np

from azulero.image import io
from azulero.tools.timing import Timer


@dataclass
class Scale:
    width: float
    text: str
    height: int = 5
    margin_right: int = 50
    margin_bottom: int = 50
    margin_text: int = 10
    font_scale: float = 1
    color: tuple = (255, 255, 255)

    def draw(self, image, zoom):
        self._draw_line(image, zoom)
        if self.text:
            self._draw_text(image)

    def _draw_line(self, image, zoom):
        tmp = np.ascontiguousarray(image, dtype=np.uint8)
        stop = np.array(
            [image.shape[1] - self.margin_right, image.shape[0] - self.margin_bottom],
            dtype=int,
        )
        start = stop - np.array(
            [np.round(self.width * zoom / 100), self.height], dtype=int
        )
        cv2.rectangle(tmp, start, stop, self.color, -1)  # type: ignore
        image[:] = tmp[:]

    def _draw_text(self, image):
        tmp = np.ascontiguousarray(image, dtype=np.uint8)
        pos = [
            image.shape[1] - self.margin_right,
            image.shape[0] - self.margin_bottom - self.height - self.margin_text,
        ]
        pos[0] -= cv2.getTextSize(
            self.text, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, 2
        )[0][0]
        cv2.putText(
            tmp,
            self.text,
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            self.font_scale,
            self.color,
            2,
        )
        image[:] = tmp[:]


class Footprints:

    def __init__(self, wcs, catalog, pfa=0.01):
        self.wcs = wcs
        filtered = catalog[
            (catalog["SPURIOUS_FLAG"] == 0) & (catalog["POINT_LIKE_PROB"] < pfa)
        ]
        self.ra = self._read_column(filtered, "RIGHT_ASCENSION")
        self.dec = self._read_column(filtered, "DECLINATION")
        self.half_a = self._read_column(filtered, "SEMIMAJOR_AXIS")
        self.e = self._read_column(filtered, "ELLIPTICITY")
        self.angle = self._read_column(filtered, "POSITION_ANGLE")
        self.factor = 1.5  # Corresponds to SExtractor
        self.color = (255, 255, 255)
        self.thickness = 3

    def _read_column(self, catalog, name):
        return np.array(catalog[name].data, dtype=float)

    def draw(self, image):
        tmp = np.ascontiguousarray(image, dtype=np.uint8)
        coords = SkyCoord(ra=self.ra, dec=self.dec, unit="deg", frame="icrs")
        x, y = self.wcs.world_to_pixel(coords)
        a = 2 * self.half_a * self.factor
        b = a * (1 - self.e)
        angle = self.angle
        count = 0
        for params in zip(x, y, a, b, angle):
            if not np.isnan(params).any():
                self._draw_ellipse(tmp, *params)
                count += 1
        image[:] = tmp[:]
        return count

    def _draw_ellipse(self, image, x, y, a, b, angle):
        shift = 3  # Decimal precision as power of 2
        center = (int(round(x * 2**shift)), int(round(y * 2**shift)))
        axes = (int(round(a * 2**shift)), int(round(b * 2**shift)))
        cv2.ellipse(
            image,
            center,
            axes,
            angle + 90,
            0,
            360,
            self.color,
            self.thickness,
            cv2.LINE_AA,
            shift,
        )


def read_wcs(path):
    with fits.open(path) as hdul:
        header = hdul[0].header  # type: ignore
    return wcs.WCS(header)


def read_catalog(path):
    with fits.open(path) as hdul:
        data = hdul[1].data  # type: ignore
    return data


def add_parser(subparsers, help):

    parser = subparsers.add_parser(
        "overlay",
        help=help,
        description="Overlay an image with source detections.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "tile",
        type=str,
        metavar="INDEX",
        help="Tile index.",
    )
    parser.add_argument(
        "--pfa",
        type=float,
        default=0.01,
        metavar="PROBABILITY",
        help="Probability of false alarm.",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="TEMPLATE",
        default="{workspace}/{tile}/{tile}_overlay.png",
        help="Output filename",
    )

    parser.set_defaults(func=run)


def run(args):

    timer = Timer()
    workdir = Path(args.workspace) / args.tile
    image_path = next(workdir.glob("*VIS*.fits"))
    catalog_path = next(workdir.glob("*FINAL-CAT*.fits"))
    output_path = Path(args.output.format(workspace=args.workspace, tile=args.tile))

    print("Read inputs")
    print(f"- WCS: {image_path.name}")
    wcs = read_wcs(image_path)
    print(f"- Image: {image_path.name}")
    assert wcs.array_shape is not None
    image = np.zeros((wcs.array_shape[1], wcs.array_shape[0], 3), dtype=np.uint8)
    print(f"- Catalog: {catalog_path.name}")
    catalog = read_catalog(catalog_path)
    timer.tic_log()

    print("Draw ellipses")
    footprints = Footprints(wcs, catalog, args.pfa)
    count = footprints.draw(image)
    print(f"- Objects: {count}")
    timer.tic_log()
    print(f"- Save output: {output_path.name}")
    io.write_rgb(image, output_path, norm_depth=1)
    timer.tic_log()
