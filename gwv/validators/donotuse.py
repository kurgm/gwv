# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DO_NOT_USE="0",  # do-not-use が引用されている
)


filters = {
    "alias": {False},
    "category": default_filters["category"]
}


class DonotuseValidator(Validator):

    name = "donotuse"

    def is_invalid(self, name, related, kage, gdata, dump):
        quotings = []
        for line in kage.lines:
            if line.data[0] != 99:
                continue
            r = dump.get(line.data[7].split("@")[0])
            if r and "do-not-use" in r[1]:
                quotings.append(line.data[7])
        return [error_codes.DO_NOT_USE] + quotings or False


validator_class = DonotuseValidator
