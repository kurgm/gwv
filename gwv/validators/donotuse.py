# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.validators import filters as default_filters
from gwv.validators import ValidatorClass

filters = {
    "alias": {False},
    "category": default_filters["category"]
}


class Validator(ValidatorClass):

    name = "donotuse"

    def is_invalid(self, name, related, kage, gdata, dump):
        quotings = []
        for line in kage.lines:
            if line.data[0] != 99:
                continue
            r = dump.get(line.data[7].split("@")[0])
            if r and "do-not-use" in r[1]:
                quotings.append(line.data[7])
        return quotings or False

    def record(self, glyphname, error):
        key = "0"
        if key not in self.results:
            self.results[key] = []
        self.results[key].append([glyphname] + error)
