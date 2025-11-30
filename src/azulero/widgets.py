# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import cv2
from dataclasses import dataclass
import numpy as np


@dataclass
class Scale:
    value: str = "1 arcmin"
    width: float = 600
    height: int = 5
    margin_right: int = 50
    margin_bottom: int = 50
    margin_text: int = 10
    font_scale: float = 1
    color: tuple = (255, 255, 255)

    def draw(self, image, zoom):
        self._draw_line(image, zoom)
        self._draw_text(image)

    def _draw_line(self, image, zoom):
        stop = np.array(
            [image.shape[1] - self.margin_right, image.shape[0] - self.margin_bottom],
            dtype=int,
        )
        start = stop - np.array(
            [np.round(self.width * zoom / 100), self.height], dtype=int
        )
        cv2.rectangle(image, start, stop, self.color, -1)

    def _draw_text(self, image):
        pos = [
            image.shape[1] - self.margin_right,
            image.shape[0] - self.margin_bottom - self.height - self.margin_text,
        ]
        pos[0] -= cv2.getTextSize(
            self.value, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, 2
        )[0][0]
        cv2.putText(
            image,
            self.value,
            pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            self.font_scale,
            self.color,
            2,
        )
