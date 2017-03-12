# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math


def kageInt(s):
    """Imitates Math.floor in ECMAScript (returns an int).

    KAGE Engine uses Math.floor to parse numbers in KAGE data.
    """
    if isinstance(s, str):
        s = s.strip()
        if s == "":
            return 0
    elif isinstance(s, float):
        return int(math.floor(s))
    try:
        # decimal integer literal (may have leading 0 digits)
        return int(s)
    except ValueError:
        try:
            # hexadecimal, octal, binary integer literal
            return int(s, 0)
        except ValueError:
            # contains decimal point and/or exponent part
            return int(math.floor(float(s)))


def kageIntSuppressError(s):
    """The same as kageInt except that it returns None when s is invalid"""
    try:
        return kageInt(s)
    except (ValueError, OverflowError):
        return None


class KageData(object):

    def __init__(self, data):
        self.lines = tuple([KageLine(i, l)
                            for i, l in enumerate(data.split("$"))])
        self.len = len(self.lines)

    def isAlias(self):
        return self.len == 1 and self.lines[0].strdata[:19] == "99:0:0:0:0:200:200:"


class KageLine(object):

    def __init__(self, line_number, data):
        self.line_number = line_number
        self.strdata = data
        sdata = data.split(":")
        if kageIntSuppressError(sdata[0]) != 99:
            self.data = tuple([kageIntSuppressError(x) for x in sdata])
        else:
            self.data = tuple(
                [kageIntSuppressError(x) if i != 7 else x for i, x in enumerate(sdata)])