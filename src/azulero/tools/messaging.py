# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from functools import lru_cache
import logging
import os
import shlex
import sys


def parse_envargs(command=None, prefix=os.environ.get("AZULERO_PREFIX", "AZUL")):
    if command is None:
        prefix += "_"
    else:
        prefix += command.upper() + "_"
    args = {
        var.removeprefix(prefix).lower(): os.environ[var]
        for var in os.environ
        if var.startswith(prefix)
    }
    return args


@lru_cache
def read_pipe_args():
    if not sys.stdin.isatty():
        args = shlex.split(sys.stdin.read())  # str.split won't work with quotes
        return args
    return []


def write_pipe_args(args, log=True):
    if args and log:
        logger.header(1, "Output")
        for a in args:
            logger.bullet(str(a))
    if not sys.stdout.isatty():
        print("\n".join(shlex.quote(str(a)) for a in args))
        return True
    return False


def supports_color():
    """
    Check whether stderr supports color tags.
    """
    # Inspired from Django https://github.com/django/django/blob/main/django/core/management/color.py
    return sys.stderr.isatty() and (
        sys.platform != "win32"
        or "ANSICON" in os.environ
        or os.environ.get("TERM_PROGRAM") == "vscode"
    )


def colorize(code, message):
    """
    Add color tags to a message if stderr supports them.
    """
    return f"\x1b[{code}m{message}\x1b[0m" if supports_color() else message


class _LogFormatter(logging.Formatter):

    def __init__(self, sep=" - "):
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


header_color_codes = {1: "92;1", 2: "96;1", 3: "94;1"}


def _log_header(self, level, message, linebreaks=[1]):
    for _ in range(linebreaks[0]):
        self.info("")
    self.info(colorize(header_color_codes.get(level, "0"), message))
    for _ in range(linebreaks[-1]):
        self.info("")


def _log_bullet(self, message, symbol="•"):
    self.info(f"{symbol} {message}")


def _log_command(self, command):
    self.info("")
    self.info("You may now run:")
    self.info("")
    self.info(command)
    self.info("")


def _setup_logger():
    global logger
    logger = logging.getLogger("azulero")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_LogFormatter())
    logger.addHandler(handler)
    setattr(logging.getLoggerClass(), "header", _log_header)
    setattr(logging.getLoggerClass(), "command", _log_command)
    setattr(logging.getLoggerClass(), "bullet", _log_bullet)
    return logger


def progress_str(sequence, format="[{i}/{n}]"):
    """
    Generate a progress string in addition to the element when iterating over a sequence.
    """
    i = 1
    n = len(sequence)
    for e in sequence:
        yield format.format(i=i, n=n), e
        i += 1


logger = _setup_logger()  #: Stderr logger with support for headers and bullet lists
