#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from gwv import version
from validator import validate


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    import argparse
    parser = argparse.ArgumentParser(description="GlyphWiki data validator")
    parser.add_argument("dumpfile")
    parser.add_argument("-o", "--out", help="File to write the output JSON to")
    parser.add_argument("-n", "--names", nargs="*", help="Names of validators")
    parser.add_argument("-v", "--version", action="store_true", help="Names of validators")
    opts = parser.parse_args(args)

    if opts.version:
        print(version)
        return

    outpath = opts.out or os.path.join(os.path.dirname(opts.dumpfile), "gwv_result.json")
    dumpfile = open(opts.dumpfile)

    result = validate(dumpfile, opts.names or None)

    with open(outpath, "w") as outfile:
        outfile.write(result)


if __name__ == '__main__':
    main()
