# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import Angle
import numpy as np


class ParseError(Exception):

    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text

    def __str__(self):
        return f"Cannot parse {self.name}: {self.text}"


def match_suffix(suffix: str, text: str):
    """
    Test whether a string ends with some suffix.
    If it does, return the beginning of the string.
    Otherwise, return `None`.
    """
    text = text.strip()
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return None


def parse_length(text: str, reference: float | None = None):
    """
    Parse a length in pixels (suffix `px`) or as a percentage of a reference length (suffix `%`).
    If the length is negative, backward indexing is assumed.
    """
    if match := match_suffix("%", text):
        if reference is None:
            raise ParseError("relative length", text)
        px = float(match) / 100 * reference
    elif match := match_suffix("px", text):
        px = float(match)
    else:
        raise ParseError("length", text)
    if px < 0 and reference is not None:
        px += reference
    return px


def parse_angle(text):
    if match := match_suffix("pi", text):
        return Angle(float(match) * 180, unit="deg")
    try:
        return Angle(text)
    except Exception:
        raise ParseError("angle", text)


def parse_length_or_angle(text: str, reference: float | None = None):
    try:
        return parse_length(text, reference)
    except ParseError:
        return parse_angle(text)


def parse_lengths_or_angles(text: str, references: tuple | None = None):
    chunks = text.split(",")
    if references is None:
        values = [parse_length_or_angle(c) for c in chunks]
    elif len(chunks) != len(references):
        raise ParseError("lengths or angles", text)
    else:
        values = [parse_length_or_angle(c, r) for c, r in zip(chunks, references)]
    if isinstance(values[0], Angle):
        return Angle(values)
    else:
        return np.array(values)
