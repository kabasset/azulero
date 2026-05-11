# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Workspace:

    workspace: Path
    input_pattern: str
    channel_names: list
    output_template: str

    @classmethod
    def from_args(cls, args):
        """
        Parse command line arguments.
        """
        return cls(args.workspace, args.input, args.channels, args.output)

    def relative_to_workspace(self, path: Path) -> Path:
        """
        Return a path relative to the workspace.

        If the input path is not in the workspace, return the path unchanged.
        """
        if path.is_relative_to(self.workspace):
            return path.relative_to(self.workspace)
        return path
