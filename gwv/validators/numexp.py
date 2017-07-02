# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.validators import filters as default_filters
from gwv.validators import Validator

filters = {
    "alias": {True, False},
    "category": default_filters["category"]
}

_re_valid_chars = re.compile(r"^[\da-z_\:@-]+$")


class NumexpValidator(Validator):

    name = "numexp"

    def is_invalid(self, name, related, kage, gdata, dump):
        for i, line in enumerate(gdata.split("$")):
            if line == "":
                return [0, [i, line]]  # 空行
            if not _re_valid_chars.match(line):
                return [1, [i, line]]  # 不正な文字
            data = line.split(":")
            for j, col in enumerate(data):
                if j == 7 and data[0] == "99":
                    continue
                try:
                    numdata = int(col)
                except ValueError:
                    return [2, [i, line]]  # 整数として解釈できない
                if str(numdata) != col:
                    return [3, [i, line]]  # 不正な数値の表現
        return False


validator_class = NumexpValidator
