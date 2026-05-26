# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import cv2

from azulero import overlay
from azulero.image import io
from azulero.projections.equirectangular import Projection  # FIXME
from azulero.projections.wcs import capture_frame as wcs_frame
from azulero.tools.messaging import logger, read_pipe_args, write_pipe_args
from azulero.tools.timing import Timer
from azulero.tools.workspace import Workspace
from azulero.video import sequence
from azulero.video.gaiasky import roam_gaiasky

supported_codecs = {".mp4": "mp4v", ".avi": "xvid", ".mkv": "ffv1"}


def fourcc(path: Path):
    ext = path.suffix.lower()
    return cv2.VideoWriter_fourcc(*supported_codecs[ext])


def add_parser(subparsers, help):
    parser = subparsers.add_parser(
        "roam",
        help=help,
        description="""
        Supply an image (or a list of images), specify viewport parameters at given key frames.
        They will be interpolated to render a smooth roaming video.

        For full-sky views, an interface to Gaia Sky is available.
        To use it, first start Gaia Sky and then execute this script with option ``--gaiasky``.
        """,
        usage="%(prog)s <images> [options]",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "images",
        type=str,
        nargs="*",
        default=read_pipe_args(),
        help="Space separated list of image files or any name for Gaia Sky.",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--ortho",
        metavar="PATH",
        help="""
        Key frame sequence file for orthographic projection.
        Only scaling and rotation are performed.
        The key frames may be specified as image coordinates,
        or as sky coordinates if the images come with WCS parameters,
        or as a mix of image and sky coordinates.
        """,
    )
    group.add_argument(
        "--wcs",
        metavar="PATH",
        help="""
        Sequence file for WCS projection.
        The input images must come with WCS parameters,
        and only sky coordinates are supported.
        """,
    )
    group.add_argument(
        "--equi",
        metavar="PATH",
        help="""
        Sequence file for equirectangular sky maps.
        The input images must be equirectangular with:

        * RA from -180° on the right to 180° on the left,
        * declination from -90° at the bottom to 90° at the top.

        Only sky coordinates are supported.
        """,
    )
    group.add_argument(
        "--gaiasky",
        metavar="PATH",
        help="""
        Sequence file for Gaia Sky.
        Only sky coordinates are supported.

        WARNING: Gaia Sky has to be running before you execute this script!
        You will be asked to close the application when frames have been generated.
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="{workspace}/{sequence}_{image}.mkv",
        metavar="TEMPLATE",
        help=(
            """
            Output video file template, where:
            
            * `{workspace}` is replaced by the workspace path,
            * `{image}` is replaced by the image file stem,
            * `{sequence}` is replaced by the sequence file stem.

            """
            f"Supported extensions are: {', '.join(supported_codecs)}. "
            f"Only the MKV compression is lossless."
        ),
    )
    parser.add_argument(
        "--format",
        type=str,
        default="2K",
        metavar="WIDTH,HEIGHT",
        help="""
        Video format as comma-separated width and height or format name.
        Format names are numbers followed by `K` like `2K` for 1920 x 1080 pixels
        or `4K` for 3840 x 2160 pixels.
        """,
    )
    parser.add_argument(
        "--fps", type=float, default=25, metavar="FPS", help="Frames per second."
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        metavar="FRAME",
        help="Index of the first frame to be rendered.",
    )
    parser.add_argument(
        "--stop",
        type=int,
        default=None,
        metavar="FRAME",
        help="Index of the last frame to be rendered.",
    )
    parser.add_argument(
        "--scale",
        type=str,
        default=None,
        metavar=("LENGTH,TEXT"),
        help="Comma-separated scale length in image pixels and optional text above.",
    )

    parser.set_defaults(func=run)


def parse_format(text):
    if "," in text:
        w, h = text.split(",")
    elif value := sequence.match_suffix("K", text):
        w = float(value) * 960
        h = float(value) * 540
    else:
        raise RuntimeError(f"Unrecognized format: {text}")
    return int(w), int(h)


def run(args):

    ios = Workspace.from_args(args)
    input = ios.workspace / args.images[0]  # FIXME loop over inputs
    config = Path(args.ortho or args.wcs or args.equi or args.gaiasky)
    output = Path(
        ios.output_template.format(
            workspace=ios.workspace, image=input.stem, sequence=config.stem
        )
    )

    timer = Timer()

    if args.gaiasky:
        image_shape = [0, 0]
    else:
        logger.header(2, f"Read input image: {input.name}")
        image, wcs = io.read_product(input)
        image_shape = image.shape[:2]
        logger.bullet(f"Shape: {image_shape[0]} x {image_shape[1]}")
        pyramid = Pyramid(image, 8)  # TODO deduce amount from shape and format
        logger.bullet(f"Pyramid levels: {len(pyramid)}")
        timer.tic_log()

    logger.header(2, f"Read sequence of key frames: {config.name}")
    video_format = parse_format(args.format)
    logger.bullet(f"Video format: {video_format[0]} x {video_format[1]}")
    params = sequence.read_key_frames(
        ios.workspace / config, image_shape, args.fps, video_format
    )
    logger.bullet(f"Key frames: {len(params)}")
    centers = sequence.sin_sequence(params.centers)
    hfovs = sequence.sin_sequence(params.hfovs)
    orientations = sequence.sin_sequence(params.orientations)
    logger.bullet(f"Total frames: {len(centers)}")
    params = [
        sequence.Frame(i, c, z, a)
        for i, c, z, a in zip(range(len(centers)), centers, hfovs, orientations)
    ][args.start : args.stop]
    logger.bullet(f"Rendering range: [{args.start}, {args.stop})")
    timer.tic_log()

    if args.scale is None:
        scale = overlay.Scale(width=0, text="")
    elif not args.scale:
        scale = overlay.Scale(width=600, text="1 arcmin")  # FIXME from WCS
    elif "," not in args.scale:
        scale = overlay.Scale(width=int(args.scale), text="")
    else:
        w, t = args.scale.split(",")
        scale = overlay.Scale(width=int(w), text=t)

    logger.header(2, f"Generate frames")
    if args.gaiasky:
        logger.bullet("Run Gaia Sky")
        gaia_frames = roam_gaiasky(params, args.fps, video_format, output)
        logger.bullet("Combine frames")

    writer = cv2.VideoWriter(output, fourcc(output), args.fps, video_format)
    for i, p in enumerate(params):
        logger.bullet(f"{p} [{i+1}/{len(params)}]")
        if args.gaiasky:
            frame = cv2.imread(gaia_frames[i], cv2.IMREAD_COLOR)  # FIXME read_data
        elif args.equi:
            frame = crop_equirectangular(image, p, video_format)
        elif args.wcs:
            frame = wcs_frame(image, wcs, video_format, p)
        else:
            # FIXME assert args.ortho
            frame = crop_pyramid(pyramid, p.planar(wcs, image_shape), video_format)
        if scale.width > 0:
            scale.draw(frame, 100.0 * p.hfov)
        writer.write(np.flipud(frame))

    writer.release()
    logger.bullet(f"Wrote: {output.name}")
    timer.tic_log()

    write_pipe_args([ios.relative_to_workspace(output)])


class Pyramid:

    def __init__(self, image: np.ndarray, factor: int):
        current = 1
        self.images = {current: image}
        w = image.shape[1]
        h = image.shape[0]
        while current < factor:
            previous = self.images[current]
            current *= 2
            self.images[current] = cv2.pyrDown(
                previous, dstsize=(w // current, h // current)
            )

    def __len__(self):
        return len(self.images)

    def __getitem__(self, factor):
        return self.images[factor]

    def atleast_wide(self, extent):
        res = 1
        for factor in self.images:
            if self.images[factor].shape[1] > extent:
                res = factor
        return res


def crop_pyramid(
    pyramid: Pyramid, params: sequence.Frame, video_format: tuple[int, int]
):
    factor = pyramid.atleast_wide(
        pyramid[1].shape[1] / params.hfov * video_format[0] * 2
    )  # FIXME handle rotation
    scaled_params = sequence.Frame(
        params.index, params.center / factor, params.hfov / factor, params.orientation
    )
    return crop_planar(pyramid[factor], scaled_params, video_format)


def crop_planar(
    image: np.ndarray,
    params: sequence.Frame,
    video_format: tuple[int, int],
):
    """
    Crop a planar image according to planar parameters.
    """
    center = params.center
    scaling = video_format[0] / params.hfov
    viewport_format = np.array([params.hfov, video_format[1] / scaling])
    orientation = params.orientation_in_degrees() % 360
    viewport = cv2.RotatedRect(params.center, viewport_format, orientation)
    x0, y0, w, h = viewport.boundingRect()
    # FIXME if bbox outside image, return black frame
    vertical = w < h
    if vertical:
        # OpenCV unhappy!
        x0, y0, w, h = y0, x0, h, w
        image = np.swapaxes(image, 0, 1)
        center = np.flip(center)
    x1 = x0 + w
    y1 = y0 + h
    if x0 < 0:
        logger.warning(f"min(x) < 0 ({x0})")
        x0 = 0
    if y0 < 0:
        logger.warning(f"min(y) < 0 ({y0})")
        y0 = 0
    if x1 > image.shape[1]:
        logger.warning(f"max(x) > {image.shape[1]-1} ({x1-1})")
        x1 = image.shape[0]
    if y1 > image.shape[0]:
        logger.warning(f"max(y) > {image.shape[0]-1} ({y1-1})")
        y1 = image.shape[1]
    if x0 >= image.shape[1] or y0 >= image.shape[0] or x1 <= 0 or y1 <= 0:
        return np.zeros([video_format[1], video_format[0], 3], dtype=image.dtype)
    offset = np.array([x0, y0])
    patch = image[y0:y1, x0:x1]
    rotation = cv2.getRotationMatrix2D(center - offset, -orientation, scaling)
    rotation_format = (w, h)
    rotated_image = cv2.warpAffine(
        patch, rotation, rotation_format, flags=cv2.INTER_LINEAR
    )
    res = cv2.getRectSubPix(rotated_image, video_format, center - offset)
    if vertical:
        return np.flipud(res)
    return res


def crop_equirectangular(
    image: np.ndarray, params: sequence.Frame, video_format: tuple[int, int]
):
    """
    Project equirectangular image, adapted from py360convert.
    """
    h, w = image.shape[:2]
    hfov = np.deg2rad(params.hfov_in_degrees())
    vfov = 2 * np.atan(np.tan(hfov / 2) * h / w)
    u = float(np.deg2rad(params.center[0].value))
    v = float(np.deg2rad(params.center[1].value))
    a = float(np.deg2rad(params.orientation_in_degrees()))
    proj = Projection.from_perspective(
        (hfov, vfov),
        (u, v),
        a,
        (h, w),
        video_format,
    )
    return np.stack(
        [proj(image[..., i]).astype(np.uint8) for i in range(image.shape[2])], axis=-1
    )
