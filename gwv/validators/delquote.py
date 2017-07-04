# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.validators import filters as default_filters
from gwv.validators import Validator

filters = {
    "alias": {True, False},
    "category": default_filters["category"]
}


class DelquoteValidator(Validator):

    name = "delquote"

    def is_invalid(self, name, related, kage, gdata, dump):
        for line in kage.lines:
            if line.data[0] == 99 and line.data[7].split("@")[0] not in dump:
                return [0, line.data[7]]  # 無い部品を引用している


validator_class = DelquoteValidator
