# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.wcs import WCS
import cv2
from dataclasses import dataclass
import numpy as np


@dataclass
class Rect:
    b: int
    t: int
    l: int
    r: int

    @property
    def shape(self):
        return np.array([self.t - self.b + 1, self.r - self.l + 1])

    @property
    def bl(self):
        return (self.l, self.b)

    @property
    def br(self):
        return (self.r, self.b)

    @property
    def tl(self):
        return (self.l, self.t)

    @property
    def tr(self):
        return (self.r, self.t)

    @property
    def center(self):
        x = int((self.l + self.r) / 2 + 0.5)
        y = int((self.b + self.t) / 2 + 0.5)
        return x, y

    @property
    def corners(self):
        return [self.bl, self.br, self.tl, self.tr]


def _view_to_pix(x, y, downsampling, shape):
    return x * downsampling, (shape[0] - y - 1) * downsampling


@dataclass
class RectOverlay:

    downsampling: int
    shape: np.ndarray
    wcs: WCS
    thickness: int = 3
    color: tuple[int, int, int] = (0, 255, 0)

    def draw(self, display, rect, mode):

        self._draw_frame(display, rect)

        for c in rect.corners:
            self._draw_handle(display, c)
        self._draw_handle(display, rect.center)

        self._write_coord(display, mode, *rect.br)
        self._write_coord(display, mode, *rect.tl)
        self._write_coord(display, mode, *rect.center)

    def _draw_frame(self, canvas, rect):

        b = min(rect.b, rect.t)
        t = max(rect.b, rect.t)
        l = min(rect.l, rect.r)
        r = max(rect.l, rect.r)

        def fill_rect(p, q):
            cv2.rectangle(canvas, p, q, color=self.color, thickness=-1)

        fill_rect(
            (l - self.thickness // 2, b + self.thickness),
            (l + self.thickness // 2, t - self.thickness),
        )
        fill_rect(
            (r - self.thickness // 2, b + self.thickness),
            (r + self.thickness // 2, t - self.thickness),
        )
        fill_rect(
            (l + self.thickness, b - self.thickness // 2),
            (r - self.thickness, b + self.thickness // 2),
        )
        fill_rect(
            (l + self.thickness, t - self.thickness // 2),
            (r - self.thickness, t + self.thickness // 2),
        )

    def _draw_handle(self, canvas, p):
        x, y = p
        cv2.rectangle(
            canvas,
            (x - self.thickness, y - self.thickness),
            (x + self.thickness, y + self.thickness),
            color=self.color,
            thickness=self.thickness // 2,
        )

    def _write_coord(self, canvas, mode, x, y):
        if not mode:
            return
        x_pix, y_pix = _view_to_pix(x, y, self.downsampling, self.shape)
        if mode == 1:
            self._write_text(canvas, f"{int(x_pix)}, {int(y_pix)}", x, y)
        elif mode == 2:
            coord = self.wcs.pixel_to_world(x_pix, y_pix)
            self._write_text(
                canvas, f"{coord.ra.degree:0.3f}, {coord.dec.degree:0.3f}", x, y
            )

    def _write_text(self, canvas, text, x, y):
        cv2.putText(
            canvas,
            text,
            (x + 2 * self.thickness, y - 2 * self.thickness),
            cv2.FONT_HERSHEY_SIMPLEX,
            (self.thickness + 12) // 12,
            self.color,
            self.thickness // 2,
        )


# Adapted https://github.com/DevJom/zoner (MIT license):
# * Only one zone is drawn.
# * The zone is a rectangle.
# * Zoom center is relative to the image, not the viewport.
# * Pan-and-zoom is handled by cv2.
class RectSelector:

    def __init__(
        self, image: np.ndarray, wcs: WCS | None = None, downsampling: int = 1
    ):
        self._name = "azul crop"
        self._downsampling = downsampling
        self._image = np.flipud(image)  # OpenCV orientation
        self._shape = np.array(self._image.shape[:2])
        self._rect = Rect(0, self._shape[0] - 1, 0, self._shape[1] - 1)
        self._overlay = RectOverlay(
            self._downsampling, self._shape, wcs, min(self._shape // 500) * 2 + 3
        )

        self._dragging = False
        self._selected = ""  # e.g. "b" for bottom edge or "tl" for top-left corner
        self._snap_radius = 2 * self._overlay.thickness + 3

    @property
    def slicing(self):
        b = min(self._rect.b, self._rect.t)
        t = max(self._rect.b, self._rect.t)
        l = min(self._rect.l, self._rect.r)
        r = max(self._rect.l, self._rect.r)

        return (
            slice(
                (self._shape[0] - t - 1) * self._downsampling,
                (self._shape[0] - b) * self._downsampling,
            ),
            slice(
                l * self._downsampling,
                (r + 1) * self._downsampling,
            ),
        )

    def __call__(self):

        cv2.namedWindow(self._name, cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._name, 800, 800)
        _show_help()

        def mouse_handler(event, x, y, flags, params):

            def hovered(x_bounds, y_bounds):
                x0, x1 = x_bounds[0], x_bounds[-1]
                y0, y1 = y_bounds[0], y_bounds[-1]
                if x < x0 - self._snap_radius or x > x1 + self._snap_radius:
                    return False
                if y < y0 - self._snap_radius or y > y1 + self._snap_radius:
                    return False
                return True

            if event == cv2.EVENT_RBUTTONDOWN:
                self._selected = ""
                if hovered([self._rect.l, self._rect.r], [self._rect.b]):
                    self._selected += "b"
                elif hovered([self._rect.l, self._rect.r], [self._rect.t]):
                    self._selected += "t"
                if hovered([self._rect.l], [self._rect.b, self._rect.t]):
                    self._selected += "l"
                elif hovered([self._rect.r], [self._rect.b, self._rect.t]):
                    self._selected += "r"
                if not self._selected and hovered(
                    [self._rect.center[0]], [self._rect.center[1]]
                ):
                    self._selected += "c"
                self._dragging = bool(self._selected)

            elif event == cv2.EVENT_MOUSEMOVE:
                if self._dragging:
                    if "b" in self._selected:
                        self._rect.b = np.clip(y, 0, self._shape[0] - 1)
                    elif "t" in self._selected:
                        self._rect.t = np.clip(y, 0, self._shape[0] - 1)
                    if "l" in self._selected:
                        self._rect.l = np.clip(x, 0, self._shape[1] - 1)
                    elif "r" in self._selected:
                        self._rect.r = np.clip(x, 0, self._shape[1] - 1)
                    if self._selected == "c":
                        shape = self._rect.shape
                        bl = np.array([y, x]) - shape // 2
                        tr = bl + shape - 1
                        bl = np.clip(bl, 0, self._shape - 1)
                        tr = np.clip(tr, 0, self._shape - 1)
                        self._rect.b = bl[0]
                        self._rect.l = bl[1]
                        self._rect.t = tr[0]
                        self._rect.r = tr[1]

            elif event == cv2.EVENT_RBUTTONUP:
                self._dragging = False

        cv2.setMouseCallback(self._name, mouse_handler)

        cv2.imshow(self._name, self._image)

        mode = 1
        while True:

            k = cv2.waitKey(1)
            if k in [13, 27]:  # Enter, Escape
                break
            elif k in [ord("c"), ord("C")]:
                mode = (mode + 1) % 3
            elif k != -1:
                _show_help()
            self._draw_overlay(mode)

        cv2.destroyAllWindows()
        return self.slicing

    def _draw_overlay(self, mode):
        display = self._image.copy()
        self._overlay.draw(display, self._rect, mode)
        cv2.imshow(self._name, display)


def _show_help():
    commands = {
        "Zoom": ["Mouse wheel"],
        "Pan": ["Left mouse button"],
        "Select": ["Right mouse button"],
        "Toggle coordinates": ["C"],
        "Validate": ["Enter", "Escape"],
        "Help": ["Any other key"],
    }
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 1
    margin = 10

    shape = [0, 0]
    positions = []

    def account_text(text):
        size, baseline = cv2.getTextSize(
            text, fontFace=font, fontScale=scale, thickness=thickness
        )
        shape[0] += size[1] + baseline
        positions.append(shape[0])
        shape[1] = max(shape[1], size[0])

    for k in commands:
        account_text(k + ":")
        for v in commands[k]:
            account_text("  " + v)
    canvas = np.zeros([shape[0] + 2 * margin, shape[1] + 2 * margin, 3], dtype=np.uint8)

    def write_text(text, index):
        cv2.putText(
            canvas,
            text,
            (margin, margin + positions[index]),
            fontFace=font,
            fontScale=scale,
            color=(255, 255, 255),
            thickness=thickness,
        )

    i = 0
    for k in commands:
        write_text(k + ":", i)
        i += 1
        for v in commands[k]:
            write_text("  " + v, i)
            i += 1

    cv2.namedWindow("Help", cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_AUTOSIZE)
    cv2.imshow("Help", canvas)
