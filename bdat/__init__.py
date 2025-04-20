#!/usr/bin/env python

from . import build_cjksrc
from . import build_mj


BUILDFUNCS = [
    build_cjksrc.main,
    build_mj.main,
]


def main():
    from . import __main__

    __main__.main()


if __name__ == "__main__":
    main()
