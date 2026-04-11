# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys


def supports_color():
    # Inspired from Django https://github.com/django/django/blob/main/django/core/management/color.py
    return sys.stderr.isatty() and (
        sys.platform != "win32"
        or "ANSICON" in os.environ
        or os.environ.get("TERM_PROGRAM") == "vscode"
    )


def colorize(code, message):
    return f"\x1b[{code}m{message}\x1b[0m" if supports_color() else message


class _LogFormatter(logging.Formatter):

    def __init__(self, sep=" | "):
        super().__init__()
        self.sep = sep

    def format(self, record):

        is_debug = logger.getEffectiveLevel() < logging.INFO

        if record.levelname == "INFO" and not is_debug:
            fmt = "%(message)s"
        else:
            fmt = f"%(levelname)s{self.sep}%(message)s"

        if is_debug:
            fmt = (
                f"%(asctime)s{self.sep}%(filename)s{self.sep}%(lineno)d{self.sep}{fmt}"
            )
        self._style._fmt = self._colorize(record.levelno, fmt)
        return super().format(record)

    def _colorize(self, level, message):
        if not supports_color():
            return message
        if level >= logging.ERROR:
            return colorize("41;1", message)
        if level >= logging.WARNING:
            return colorize("31;1", message)
        return message


def _setup_logger():
    global logger
    logger = logging.getLogger("azulero")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_LogFormatter())
    logger.addHandler(handler)
    return logger


logger = _setup_logger()
