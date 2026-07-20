# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from astropy.coordinates import Angle
import numpy as np
from pathlib import Path
import re


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


def parse_target(text: str) -> tuple[Path, slice | tuple | None]:
    """
    Parse the path and slicing from a target string.
    """
    if text.endswith("]") and "[" in text:
        workdir, slicing = text.removesuffix("]").split("[")
        return Path(workdir), parse_slice(slicing)
    return Path(text), None


def parse_slice(text: str | None) -> slice | tuple | None:
    """
    Parse a slice or slice tuple from a string, e.g. ``50:70`` or ``:,3:14``.
    """
    if text is None:
        return None
    chunks = text.split(",")
    if len(chunks) == 1:
        return _parse_slice(chunks[0])
    return tuple(_parse_slice(axis) for axis in chunks)


def _parse_slice(text: str) -> slice:
    parse_index = lambda i: int(i) if i else None
    return slice(*[parse_index(i.strip()) for i in text.split(":")])


def parse_map(text: str, dtype=float) -> list[tuple[object, object]]:
    """
    Parse a comma-separated list of ``key:value`` pairs.
    """
    if not text:
        return []
    pairs = [p.split(":") for p in text.split(",")]
    return [(dtype(x), dtype(y)) for x, y in pairs]


def dump_map(curve: list):
    items = [f"{knot[0]}:{knot[1]}" for knot in curve]
    return ",".join(items)


def render_template(text: str, *args, **kwargs) -> str:
    """
    Replace placeholders in a string, possibly with fallbacks, with provided values.

    Placeholder syntax is ``{<placeholder>}`` or ``{<placeholder>|<fallback>}``.
    If ``<placeholder>`` is an integer ``i`` (resp. key ``k``), it is substituted with ``str(args[i])`` (resp. ``str(kwargs[k])``).
    Backward indexing is supported.
    If ``args[i]`` (resp. ``kwargs[k]`` does not exist, then it is replaced with the provided fallback value.
    If no fallback is provided, the placeholder is not substituted.
    """
    placeholder = lambda p: "{" + str(p) + "}"
    for i in range(-len(args), len(args)):
        text = text.replace(placeholder(i), str(args[i]))
        value = str(i) if i >= 0 else r"\-" + str(-i)
        pattern = r"\{" + value + r"\|[A-Za-z0-9_]+\}"
        text = re.sub(pattern, str(args[i]), text)
    for k in kwargs:
        text = text.replace(placeholder(k), str(kwargs[k]))
        pattern = r"\{" + str(k) + r"\|[A-Za-z0-9_]+\}"
        text = re.sub(pattern, str(kwargs[k]), text)
    pattern = r"\{\-?[A-Za-z0-9_]+\|([A-Za-z0-9_]+)\}"  # possibly negative int or str (could be more specific)
    return re.sub(pattern, r"\1", text)
