# SPDX-FileCopyrightText: Copyright (C) 2025, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

import time
import tracemalloc


class Timer(object):  # FIXME rename as profiler

    def __init__(self):
        tracemalloc.start()
        self.start = time.perf_counter()
        self.prev = self.start
        self.split = 0
        self.total = 0
        self.size = 0
        self.peak = 0

    def tic(self):
        prev = self.prev
        self.prev = time.perf_counter()
        self.split = self.prev - prev
        self.total = self.prev - self.start
        self.size, self.peak = tracemalloc.get_traced_memory()
        self.size /= 1024**3
        self.peak /= 1024**3
        tracemalloc.reset_peak()

    def tic_print(self):
        self.tic()
        print(f"- Elapsed time: {self.split:.1f}s / Total: {self.total:.1f}s")
        print(f"- Memory usage: {self.size:.1f}GB / Peak: {self.peak:.1f}GB")
