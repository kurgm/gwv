#!/usr/bin/env python

import argparse
import json
import os
import sys

from gwv.validator import validate
from gwv import version


def open_dump(filename):
    dump = {}
    with open(filename) as f:
        if filename[-4:] == ".csv":
            # first line contains the last modified time
            timestamp = int(f.readline()[:-1])
            for l in f:
                row = l.rstrip("\n").split(",")
                if len(row) != 3:
                    continue
                dump[row[0]] = (row[1], row[2])
        else:
            # dump_newest_only.txt
            timestamp = os.path.getmtime(filename)
            line = f.readline()  # header
            line = f.readline()  # ------
            while line:
                row = [x.strip() for x in line.split("|")]
                if len(row) != 3:
                    line = f.readline()
                    continue
                dump[row[0]] = (row[1], row[2])
                line = f.readline()
    return dump, timestamp


def main(args=None):
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
    dump, timestamp = open_dump(opts.dumpfile)

    result = validate(dump, opts.names or None, timestamp)

    with open(outpath, "w") as outfile:
        json.dump(result, outfile, separators=(",", ":"), sort_keys=True)


if __name__ == '__main__':
    main()
