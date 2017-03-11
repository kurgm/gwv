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


class KageData(object):

    def __init__(self, data):
        self.lines = tuple([KageLine(i, l)
                            for i, l in enumerate(data.split("$"))])
        self.len = len(self.lines)


class KageLine(object):

    def __init__(self, line_number, data):
        self.line_number = line_number
        sdata = data.split(":")
        if kageInt(sdata[0]) != 99:
            self.data = tuple([kageInt(x) for x in sdata])
        else:
            self.data = tuple(
                [kageInt(x) if i != 7 else x for i, x in enumerate(sdata)])
