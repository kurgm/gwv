from __future__ import annotations

import pathlib
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name == "sdist":
            sdist_build()


def sdist_build():
    repo_root = pathlib.Path(__file__).parent
    sys.path.append(str(repo_root))
    import bdat

    bdat.main()
