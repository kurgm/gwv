#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from gwv import version
from validator import validate


def open_dump(filename):
    dump = {}
    with open(filename) as f:
        if filename[-4:] == ".csv":
            for l in f:
                row = l.rstrip("\n").split(",")
                if len(row) != 3:
                    continue
                dump[row[0]] = (row[1], row[2])
        else:
            # dump_newest_only.txt
            line = f.readline()  # header
            line = f.readline()  # ------
            while line:
                l = [x.strip() for x in line.split("|")]
                if len(l) != 3:
                    line = f.readline()
                    continue
                dump[row[0]] = (row[1], row[2])
                line = f.readline()
    return dump


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    import argparse
    parser = argparse.ArgumentParser(description="GlyphWiki data validator")
    parser.add_argument("dumpfile")
    parser.add_argument("-o", "--out", help="File to write the output JSON to")
    parser.add_argument("-n", "--names", nargs="*", help="Names of validators")
    parser.add_argument("-v", "--version", action="store_true",
                        help="Names of validators")
    opts = parser.parse_args(args)

    if opts.version:
        print(version)
        return

    outpath = opts.out or os.path.join(
        os.path.dirname(opts.dumpfile), "gwv_result.json")
    dump = open_dump(opts.dumpfile)

    result = validate(dump, opts.names or None)

    with open(outpath, "w") as outfile:
        outfile.write(result)


if __name__ == '__main__':
    main()
