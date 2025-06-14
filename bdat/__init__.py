#!/usr/bin/env python

from __future__ import annotations

from . import build_cjksrc, build_mj

BUILDFUNCS = [
    build_cjksrc.main,
    build_mj.main,
]


def main():
    from . import __main__

    __main__.main()


if __name__ == "__main__":
    main()
