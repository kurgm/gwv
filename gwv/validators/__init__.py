# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.helper import isAlias
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.helper import isUcs

all_validator_names = []

filters = {
    "alias": {True, False},
    "category": {"user-owned", "ids", "togo", "togo-var", "gokan", "gokan-var",
                 "ucs", "ucs-var", "cdp", "koseki-kanji", "koseki-hikanji",
                 "toki", "ext", "other"}
}

_re_ids = re.compile(r"u2ff[\dab]-")
_re_cdp = re.compile(r"cdp[on]?-[\da-f]{4}(-|$)")
_re_koseki = re.compile(r"^koseki-\d{6}$")
_re_toki = re.compile(r"^toki-\d{8}$")
_re_ext = re.compile(r"^ext[df]-\d{5}$")


def _categorize(glyphname):
    if "_" in glyphname:
        return "user-owned"
    splitname = glyphname.split("-")
    header = splitname[0]
    if isUcs(header):
        if _re_ids.match(glyphname):
            return "ids"
        if isTogoKanji(header):
            return "togo" if len(splitname) == 1 else "togo-var"
        if isGokanKanji(header):
            return "gokan" if len(splitname) == 1 else "gokan-var"
        return "ucs" if len(splitname) == 1 else "ucs-var"
    if _re_cdp.match(glyphname):
        return "cdp"
    if _re_koseki.match(glyphname):
        return "koseki-hikanji" if glyphname[7] == "9" else "koseki-kanji"
    if _re_toki.match(glyphname):
        return "toki"
    if _re_ext.match(glyphname):
        return "ext"
    # TODO: add irg2015-
    return "other"


filter_funcs = {
    "alias": lambda glyphname, related, data: isAlias(data),
    "category": lambda glyphname, related, data: _categorize(glyphname)
}
