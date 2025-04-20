#!/usr/bin/env python

from __future__ import annotations

from . import BUILDFUNCS


def main():
    for buildfunc in BUILDFUNCS:
        buildfunc()


if __name__ == "__main__":
    main()
