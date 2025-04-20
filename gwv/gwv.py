#!/usr/bin/env python

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from gwv import version
from gwv.dump import Dump
from gwv.validator import validate

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(args: Sequence[str] | None = None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="GlyphWiki data validator")
    parser.add_argument("dumpfile", type=Path)
    parser.add_argument(
        "-o", "--out", help="File to write the output JSON to", type=Path
    )
    parser.add_argument(
        "--ignore-error",
        action="store_true",
        help="Ignore runtime errors and resume validation of next glyph",
    )
    parser.add_argument("-n", "--names", nargs="*", help="Names of validators")
    parser.add_argument("-v", "--version", action="version", version=version)
    opts = parser.parse_args(args)

    dump_path: Path = opts.dumpfile
    outpath: Path = opts.out or dump_path.with_name("gwv_result.json")
    dump = Dump.open(dump_path)

    result = validate(dump, opts.names or None, ignore_error=opts.ignore_error)

    with outpath.open("w") as outfile:
        json.dump(result, outfile, separators=(",", ":"), sort_keys=True)


if __name__ == "__main__":
    main()
