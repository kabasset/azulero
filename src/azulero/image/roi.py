# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import cv2
import numpy as np


# Adapted https://github.com/DevJom/zoner (MIT license):
# * Only one zone is drawn.
# * The zone is a rectangle.
# * Zoom center is relative to the image, not the viewport.
# * Pan-and-zoom is handled by cv2.
class RectSelector:

    def __init__(
        self, image: np.ndarray, downsampling: int = 1, window_name: str = "azul crop"
    ):
        self.window_name = window_name
        self.image = np.flipud(image[::downsampling, ::downsampling])
        self.downsampling = downsampling
        self.image_shape = np.array(self.image.shape[:2])
        self.region = {
            "b": 0,
            "t": self.image_shape[0] - 1,
            "l": 0,
            "r": self.image_shape[1] - 1,
        }

        self.dragging = False
        self.mouse_pos = (0, 0)
        self.selection = ""  # e.g. "b" for bottom edge or "tl" for top-left corner
        self.snap_radius = 50

    def view_to_pix(self, pos: np.ndarray):
        return np.clip(pos, 0, self.image_shape, dtype=int)

    def select(self):

        cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)

        def mouse_handler(event, x, y, flags, params):

            pos = self.view_to_pix(np.array([y, x]))

            def distance(point):
                return np.abs(point - pos)

            if event == cv2.EVENT_RBUTTONDOWN:
                self.selection = ""
                bottom, left = distance([self.region["b"], self.region["l"]])
                top, right = distance([self.region["t"], self.region["r"]])
                if bottom < self.snap_radius:
                    self.selection += "b"
                elif top < self.snap_radius:
                    self.selection += "t"
                if left < self.snap_radius:
                    self.selection += "l"
                elif right < self.snap_radius:
                    self.selection += "r"
                self.dragging = bool(self.selection)

            elif event == cv2.EVENT_MOUSEMOVE:
                self.mouse_pos = pos
                if self.dragging:
                    if "b" in self.selection:
                        self.region["b"] = pos[0]
                    elif "t" in self.selection:
                        self.region["t"] = pos[0]
                    if "l" in self.selection:
                        self.region["l"] = pos[1]
                    if "r" in self.selection:
                        self.region["r"] = pos[1]

            elif event == cv2.EVENT_RBUTTONUP:
                self.dragging = False
                print(self.slicing())

        cv2.setMouseCallback(self.window_name, mouse_handler)

        cv2.imshow(self.window_name, self.image)

        while True:

            display = self.image.copy()
            cv2.rectangle(
                display,
                (self.region["l"], self.region["b"]),
                (self.region["r"], self.region["t"]),
                color=(0, 255, 0),
                thickness=4,
            )
            k = cv2.waitKey(1)
            if k == 13 or k == 27:  # Enter or Escape
                break
            try:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 0:
                    break
            except:
                break
            cv2.imshow(self.window_name, display)

        cv2.destroyAllWindows()
        return self.slicing()

    def slicing(self):
        return (
            slice(
                (self.image_shape[0] - self.region["t"]) * self.downsampling - 1,
                (self.image_shape[0] - self.region["b"]) * self.downsampling,
            ),
            slice(
                self.region["l"] * self.downsampling,
                self.region["r"] * self.downsampling + 1,
            ),
        )


if __name__ == "__main__":  # FIXME rm
    path = "/home/Euclid/Downloads/DR1/102159776/Tile_102159776.tiff"
    factor = 10
    image = np.flipud(cv2.imread(path))
    sel = RectSelector(image, factor)
    rect = sel.select()
    print(rect)
