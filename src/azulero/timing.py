# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import time


class Timer(object):

    def __init__(self):
        self.start = time.perf_counter()
        self.prev = self.start

    def tic(self):
        prev = self.prev
        self.prev = time.perf_counter()
        return self.prev - prev, self.prev - self.start

    def tic_print(self):
        split, total = self.tic()
        print(f"- Elapsed: {split}s [Total: {total}s]")
