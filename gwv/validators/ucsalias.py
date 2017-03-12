# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.validators import ValidatorClass

filters = {
    "alias": {True},
    "category": {"togo", "togo-var", "gokan", "gokan-var",
                 "ucs-hikanji", "ucs-hikanji-var"}
}

_re_sources = re.compile(r"^([gtvhmi]|j[asv]?|k[pv]?|us?)$")
_re_ucs_ = re.compile(r"^u[\da-f]+(-|$)")
_re_ids = re.compile(r"^u2ff.-")


class Validator(ValidatorClass):

    name = "ucsalias"

    def is_invalid(self, name, related, kage, gdata, dump):
        entity = gdata[19:]
        if "-" in name:
            sname = name.split("-")
            len_sname = len(sname)
            if len_sname > 3:
                return False
            if len_sname == 3:
                if sname[1] not in ("var", "itaiji"):
                    return False
                if sname[0] not in dump:
                    return False  # 無印が見つからない
                nomark_data = dump[sname[0]][1].split("$")
                if len(nomark_data) == 1 and nomark_data[0][:19] == "99:0:0:0:0:200:200:":
                    nomark_entity = nomark_data[0][19:]
                else:
                    nomark_entity = sname[0]
                if sname[1] == "var":
                    # uxxxx-var-xxx が uxxxx (の実体)の別名
                    return [10, entity] if entity == nomark_entity else False
                # uxxxx-itaiji-xxx が uxxxx (の実体)の別名
                return [20, entity] if entity == nomark_entity else False
            if _re_sources.match(sname[1]):
                return [1] if entity == sname[0] else False
            return False
        if not _re_ucs_.match(entity) or _re_ids.match(entity):
            if entity == "undefined" or entity[:5] == "extf-":
                return False
            # “uxxxx”が“uyyyy-…”以外やIDSのエイリアス
            return [0, entity]
        s_entity = entity.split("-")
        if s_entity[0] == name and len(s_entity) == 3:
            if s_entity[1] == "var":
                return [11, entity]  # uxxxx が uxxxx-var-xxx    の別名
            if s_entity[1] == "itaiji":
                return [21, entity]  # uxxxx が uxxxx-itaiji-xxx の別名
        return False
