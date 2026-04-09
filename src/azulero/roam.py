# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import argparse
import numpy as np
from pathlib import Path
import cv2

from azulero import io, overlay, sequence
from azulero.equirectangular import Projection
from azulero.gaiasky import roam_gaiasky
from azulero.timing import Timer


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "roam",
        help="Create a video which pans and zooms in an image.",
        description=(
            "Supply an image, specify viewport position and parameters at given times. "
            "They will be interpolated to render a smooth roaming video."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "image",
        type=str,
        help="Input image file.",
    )
    parser.add_argument(
        "sequence",
        type=str,
        help="YAML configuration file which specifies the sequence of key frames.",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--equirectangular",
        "-e",
        action="store_true",
        help="Enable equirectangular to planar projection.",
    )
    group.add_argument(
        "--gaiasky",
        "-g",
        action="store_true",
        help="Render Gaiasky frames.",
    )
    group.add_argument(
        "--wcs",
        type=str,
        default=None,
        metavar="PATH",
        help=(
            "Path to the WCS parameters as a YAML file. "
            "This is needed to specify the center as RA/dec coordinates "
            "or the zoom as an angular field of view, "
            "unless the input has equirectangular projection."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="{workspace}/{image}_{sequence}.mkv",
        metavar="TEMPLATE",
        help="Output video file template (mkv compression is lossless, mp4 compression is lossy).",
    )
    parser.add_argument(
        "--format",
        type=int,
        nargs=2,
        default=[1920, 1080],
        metavar=("WIDTH", "HEIGHT"),
        help="Video format",
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
        nargs="*",
        default=None,
        metavar=("LENGTH", "TEXT"),
        help="Scale length in image pixels, and text above",
    )

    parser.set_defaults(func=run)


def run(args):

    input = Path(args.workspace).expanduser() / args.image
    config = Path(args.sequence)
    output = Path(
        args.output.format(
            workspace=args.workspace, image=input.with_suffix(""), sequence=config.stem
        )
    )

    timer = Timer()

    if args.gaiasky:
        image_shape = [0, 0]
    else:
        print(f"Read input image: {input.name}")
        image = cv2.imread(input, cv2.IMREAD_COLOR)
        image_shape = image.shape[:2]
        print(f"- Shape: {image_shape[0]} x {image_shape[1]}")
        pyramid = Pyramid(image, 8)
        print(f"- Pyramid levels: {len(pyramid)}")
        timer.tic_print()

    print(f"Read sequence of key frames: {config.name}")
    wcs = None if args.wcs is None else io.read_wcs(Path(args.workspace), args.wcs)
    params = sequence.read_key_frames(config, image_shape, args.fps, args.format)
    print(f"- Key frames: {len(params)}")
    centers = sequence.sin_sequence(params.centers)
    hfovs = sequence.sin_sequence(params.hfovs)
    orientations = sequence.sin_sequence(params.orientations)
    print(f"- Total frames: {len(centers)}")
    params = [
        sequence.Frame(i, c, z, a)
        for i, c, z, a in zip(range(len(centers)), centers, hfovs, orientations)
    ][args.start : args.stop]
    print(f"- Rendering range: [{args.start}, {args.stop})")
    timer.tic_print()

    if args.scale is None:
        scale = overlay.Scale(width=0, text="")
    elif len(args.scale) == 0:
        scale = overlay.Scale(width=600, text="1 arcmin")  # FIXME from WCS
    elif len(args.scale) == 1:
        scale = overlay.Scale(width=int(args.scale[0]), text="")
    elif len(args.scale) == 2:
        scale = overlay.Scale(width=int(args.scale[0]), text=args.scale[1])

    print(f"Generate frames")
    if args.gaiasky:
        print("- Run Gaia Sky")
        gaia_frames = roam_gaiasky(params, args.fps, args.format, output)

    writer = cv2.VideoWriter(output, fourcc(output), args.fps, args.format)
    for i, p in enumerate(params):
        print(f"- {p} [{i+1}/{len(params)}]")
        if args.gaiasky:
            frame = cv2.imread(gaia_frames[i], cv2.IMREAD_COLOR)
        elif args.equirectangular:
            frame = crop_equirectangular(image, p, args.format)
        else:
            frame = crop_pyramid(
                pyramid, p.planar(wcs, image_shape), args.format
            )  # FIXME this transforms p inplace
        if scale.width > 0:
            scale.draw(frame, 100.0 * p.hfov)
        writer.write(frame)

    writer.release()
    print(f"- Output written: {output}")
    timer.tic_print()


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


def fourcc(path: Path):
    ext = path.suffix.lower()
    codecs = {".mp4": "mp4v", ".avi": "xvid", ".mkv": "ffv1"}
    return cv2.VideoWriter_fourcc(*codecs[ext])


def crop_pyramid(
    pyramid: Pyramid, params: sequence.Frame, video_format: tuple[int, int]
):
    factor = pyramid.atleast_wide(
        pyramid[1].shape[1] / params.hfov * video_format[0] * 2
    )  # FIXME handle rotation
    print(
        f"- Reduction factor: {params.hfov / pyramid[1].shape[1]} -> {factor}"
    )  # FIXME rm
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
    viewport = cv2.RotatedRect(params.center, viewport_format, -orientation)
    x0, y0, w, h = viewport.boundingRect()
    # FIXME if bbox outside image, return black frame
    vertical = w < h
    if vertical:
        # OpenCV unhappy!
        x0, y0, w, h = y0, x0, h, w
        image = np.swapaxes(image, 0, 1)
        orientation = 90 - orientation
        center = np.flip(center)
    x1 = x0 + w
    y1 = y0 + h
    if x0 < 0:
        print(f"WARNING: min(x) < 0 ({x0})")
        x0 = 0
    if y0 < 0:
        print(f"WARNING: min(y) < 0 ({y0})")
        y0 = 0
    if x1 > image.shape[1]:
        print(f"WARNING: max(x) > {image.shape[1]-1} ({x1-1})")
        x1 = image.shape[0]
    if y1 > image.shape[0]:
        print(f"WARNING: max(y) > {image.shape[0]-1} ({y1-1})")
        y1 = image.shape[1]
    if x0 >= image.shape[1] or y0 >= image.shape[0] or x1 <= 0 or y1 <= 0:
        return np.zeros([video_format[1], video_format[0], 3], dtype=image.dtype)
    offset = np.array([x0, y0])
    patch = image[y0:y1, x0:x1]
    rotation = cv2.getRotationMatrix2D(center - offset, orientation, scaling)
    rotation_format = (w, h)
    rotated_image = cv2.warpAffine(
        patch, rotation, rotation_format, flags=cv2.INTER_LINEAR
    )
    res = cv2.getRectSubPix(rotated_image, video_format, center - offset)
    if vertical:
        return np.flipud(res)
    return res


def crop_equirectangular(
    image: np.ndarray, params: sequence.Frame, video_format: tuple
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
        [hfov, vfov],
        [u, v],
        a,
        [h, w],
        video_format,
    )
    return np.stack(
        [proj(image[..., i]).astype(np.uint8) for i in range(image.shape[2])], axis=-1
    )
