# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.validators import filters as default_filters
from gwv.validators import ValidatorClass

filters = {
    "alias": {False},
    "category": default_filters["category"] - {"user-owned"}
}


_re_vars = re.compile(
    r"-([gtvhmi]|k[pv]?|us?|j[asv]?)?(\d{2})(-(var|itaiji)-\d{3})?(@|$)")


class Validator(ValidatorClass):

    name = "order"

    def is_invalid(self, name, related, kage, gdata, dump):
        if kage.len == 1:
            return False
        first = kage.lines[0]
        last = kage.lines[-1]
        if first.data[0] == 99:
            fG = first.data[7]
            m = _re_vars.search(fG)
            if m:
                henka = m.group(2)
                if henka == "02":
                    return [2, fG]  # 右部品が最初
                if henka in ("04", "14", "24"):
                    return [4, fG]  # 下部品が最初
                if henka == "06":
                    return [6, fG]  # 囲み内側部品が最初
        if last.data[0] == 99:
            lG = last.data[7]
            m = _re_vars.search(lG)
            if m:
                henka = m.group(2)
                if henka == "01":
                    return [11, lG]  # 左部品が最後
                if henka == "03":
                    return [13, lG]  # 上部品が最後
                if henka in ("05", "10", "11", "15"):
                    return [15, lG]  # 囲み外側部品が最初
