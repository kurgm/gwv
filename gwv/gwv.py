#!/usr/bin/env python

import argparse
import json
import os
import sys
from typing import Optional, Sequence

from gwv.dump import Dump
from gwv.validator import validate
from gwv import version


def main(args: Optional[Sequence[str]] = None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="GlyphWiki data validator")
    parser.add_argument("dumpfile")
    parser.add_argument("-o", "--out", help="File to write the output JSON to")
    parser.add_argument("-n", "--names", nargs="*", help="Names of validators")
    parser.add_argument("-v", "--version", action="version", version=version)
    opts = parser.parse_args(args)

    outpath = opts.out or os.path.join(
        os.path.dirname(opts.dumpfile), "gwv_result.json")
    dump = Dump.open(opts.dumpfile)

    result = validate(dump, opts.names or None)

    with open(outpath, "w") as outfile:
        json.dump(result, outfile, separators=(",", ":"), sort_keys=True)


if __name__ == '__main__':
    main()
