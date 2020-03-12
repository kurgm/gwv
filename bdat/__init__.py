#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from . import build_cjksrc
from . import build_mj


BUILDFUNCS = [
    build_cjksrc.main,
    build_mj.main,
]


def main():
    for buildfunc in BUILDFUNCS:
        buildfunc()


if __name__ == "__main__":
    main()
