# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Workspace:

    workspace: Path = Path(".")
    input_pattern: str = "*[-_]{channel}[-_]*.fits"
    channel_names: tuple = ("VIS", "NIR-Y", "NIR-J", "NIR-H")
    output_template: str = "{workspace}/{workdir}/{1|Tile}_{0}.tiff"

    @classmethod
    def from_args(cls, args):
        """
        Parse command line arguments.
        """
        workspace = Path(args.workspace).expanduser().resolve()
        return cls(workspace, args.input, args.channels, args.output)

    def relative_to_workspace(self, path: Path) -> Path:
        """
        Return a path relative to the workspace.

        If the input path is not in the workspace, return the path unchanged.
        """
        if path.is_relative_to(self.workspace):
            return path.relative_to(self.workspace)
        return path
