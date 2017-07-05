# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    BASE_NOT_FOUND="0",  # 派生元が無い
)


filters = {
    "alias": {True, False},
    "category": {"ids", "togo-var", "gokan-var", "ucs-hikanji-var", "cdp", "other"}
}

_re_var_nnn_henka = re.compile(r"^(.+)-((var|itaiji)-\d{3}|\d{2})$")
_re_var_src_henka = re.compile(r"^(u[0-9a-f]{4,5}-([gtvhmi]|k[pv]?|us?|j[asv]?))(\d{2})$")
_re_var_other = re.compile(r"^(u[0-9a-f]{4,5}|cdp[on]?-[0-9a-f]{4})-")


class DelvarValidator(Validator):

    name = "delvar"

    def is_invalid(self, name, related, kage, gdata, dump):
        m = _re_var_nnn_henka.match(name) or _re_var_src_henka.match(name) or \
            _re_var_other.match(name)
        if m:
            prefix = m.group(1)
            if prefix not in dump:
                return [error_codes.BASE_NOT_FOUND, prefix]  # 派生元が無い
        return None


validator_class = DelvarValidator
