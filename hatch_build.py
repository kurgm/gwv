from __future__ import annotations

import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        repo_root = Path(__file__).parent
        sys.path.append(str(repo_root))
        import bdat

        bdat.main()
