# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.helper import cjk_sources
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.validators import ValidatorClass

filters = {
    "alias": {True, False},
    "category": {"togo", "togo-var", "gokan", "gokan-var"}
}


class Validator(ValidatorClass):

    name = "related"

    def is_invalid(self, name, related, kage, gdata, dump):
        expected_related = name.split("-")[0]
        if isGokanKanji(expected_related):
            u = cjk_sources.get(expected_related, cjk_sources.COLUMN_COMPATIBILITY_VARIANT)
            if u is None:
                return False
            expected_related = "u" + u[2:].lower()

        if related != "u3013" and expected_related != related:
            return [0, related, expected_related]  # 間違った関連字

        if kage.isAlias():
            entity_name = gdata[19:]
            entity_header = entity_name.split("-")[0]
            if isTogoKanji(entity_header) or entity_header == "extf":
                return False
            if entity_name not in dump:
                return [2, entity_name]  # 実体が存在しない

            related = dump[entity_name][0]
            if related == "u3013":
                return [11, entity_name, expected_related]  # 実体が関連字なし

            if expected_related != related:
                return [10, entity_name, related, expected_related]  # 実体の関連字が違う

        elif related == "u3013":
            return [1, expected_related]  # 関連字なし

        return False
