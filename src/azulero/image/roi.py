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
        self._name = window_name
        self._downsampling = downsampling
        self._image = np.flipud(
            image[:: self._downsampling, :: self._downsampling]
        )  # OpenCV orientation
        self._shape = np.array(self._image.shape[:2])
        self._region = {
            "b": 0,
            "t": self._shape[0] - 1,
            "l": 0,
            "r": self._shape[1] - 1,
        }

        self._dragging = False
        self._selected = ""  # e.g. "b" for bottom edge or "tl" for top-left corner
        self._snap_radius = 50

    @property
    def slicing(self):
        return (
            slice(
                (self._shape[0] - self._region["t"] - 1) * self._downsampling,
                (self._shape[0] - self._region["b"]) * self._downsampling,
            ),
            slice(
                self._region["l"] * self._downsampling,
                (self._region["r"] + 1) * self._downsampling,
            ),
        )

    def __call__(self):

        cv2.namedWindow(self._name, cv2.WINDOW_GUI_NORMAL)

        def mouse_handler(event, x, y, flags, params):

            pos = np.clip([y, x], 0, self._shape - 1, dtype=int)

            def distance(point):
                return np.abs(point - pos)

            if event == cv2.EVENT_RBUTTONDOWN:
                self._selected = ""
                bottom, left = distance([self._region["b"], self._region["l"]])
                top, right = distance([self._region["t"], self._region["r"]])
                if bottom < self._snap_radius:
                    self._selected += "b"
                elif top < self._snap_radius:
                    self._selected += "t"
                if left < self._snap_radius:
                    self._selected += "l"
                elif right < self._snap_radius:
                    self._selected += "r"
                self._dragging = bool(self._selected)

            elif event == cv2.EVENT_MOUSEMOVE:
                if self._dragging:
                    if "b" in self._selected:
                        self._region["b"] = pos[0]
                    elif "t" in self._selected:
                        self._region["t"] = pos[0]
                    if "l" in self._selected:
                        self._region["l"] = pos[1]
                    if "r" in self._selected:
                        self._region["r"] = pos[1]

            elif event == cv2.EVENT_RBUTTONUP:
                self._dragging = False
                print(self.slicing)

        cv2.setMouseCallback(self._name, mouse_handler)

        cv2.imshow(self._name, self._image)

        while True:

            k = cv2.waitKey(1)
            if k == 13 or k == 27:  # Enter or Escape
                break
            try:
                if cv2.getWindowProperty(self._name, cv2.WND_PROP_VISIBLE) < 0:
                    break
            except:
                break

            self._overlay()

        cv2.destroyAllWindows()
        return self.slicing

    def _overlay(self):
        display = self._image.copy()

        thickness = max(min(self._shape) // 1000, 1) * 2 + 1
        radius = thickness
        color = (0, 255, 0)

        # cv2.rectangle(
        #     display,
        #     (self._region["l"], self._region["b"]),
        #     (self._region["r"], self._region["t"]),
        #     color=color,
        #     thickness=thickness,
        # )

        cv2.rectangle(
            display,
            (self._region["l"] - thickness // 2, self._region["b"] + radius),
            (self._region["l"] + thickness // 2, self._region["t"] - radius),
            color=color,
            thickness=-1,
        )
        cv2.rectangle(
            display,
            (self._region["r"] - thickness // 2, self._region["b"] + radius),
            (self._region["r"] + thickness // 2, self._region["t"] - radius),
            color=color,
            thickness=-1,
        )
        cv2.rectangle(
            display,
            (self._region["l"] + radius, self._region["b"] - thickness // 2),
            (self._region["r"] - radius, self._region["b"] + thickness // 2),
            color=color,
            thickness=-1,
        )
        cv2.rectangle(
            display,
            (self._region["l"] + radius, self._region["t"] - thickness // 2),
            (self._region["r"] - radius, self._region["t"] + thickness // 2),
            color=color,
            thickness=-1,
        )

        for h in "lr":
            for v in "bt":
                cv2.rectangle(
                    display,
                    (self._region[h] - radius, self._region[v] - radius),
                    (self._region[h] + radius, self._region[v] + radius),
                    color=color,
                    thickness=1,
                )
        cv2.imshow(self._name, display)


if __name__ == "__main__":  # FIXME rm
    path = "/home/basseta/Downloads/102087229/NGC128.jpg"
    factor = 8
    image = np.flipud(cv2.imread(path))
    select = RectSelector(image, factor)
    rect = select()  # TODO stretching
    print(rect)
