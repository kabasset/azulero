# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import logging
import sys


logger = logging.getLogger("azulero")


class _LogFormatter(logging.Formatter):

    def __init__(self, level, sep=" | "):
        super().__init__()
        self.levelname = level
        self.sep = sep

    def format(self, record):

        if record.levelname == "INFO" and self.levelname != "DEBUG":
            fmt = "%(message)s"
        else:
            fmt = f"%(levelname)s{self.sep}%(message)s"

        if self.levelname == "DEBUG":
            fmt = (
                f"%(asctime)s{self.sep}%(filename)s{self.sep}%(lineno)d{self.sep}{fmt}"
            )
        self._style._fmt = fmt
        return super().format(record)


def setup_logger(level):
    global logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_LogFormatter(level))
    logger.setLevel(level=level.upper())
    logger.addHandler(handler)
    return logger
