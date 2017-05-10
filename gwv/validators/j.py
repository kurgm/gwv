# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.helper import cjk_sources
from gwv.helper import GWGroupLazyLoader
from gwv.helper import load_package_data
from gwv.kagedata import KageData
from gwv.validators import ValidatorClass

filters = {
    "alias": {True, False},
    "category": {"togo", "togo-var", "gokan-var", "ext"}
}


jv_data = load_package_data("data/jv.json")
jv_no_use_part_replacement = {
    no_use: use
    for use, no_uses in jv_data["no-use-part"].items()
    for no_use in no_uses
}
jv_no_apply_parts = set(jv_data["no-apply-jv"])


def checkJV(kage):
    used_parts = [kageline.data[7].split("@")[0]
                  for kageline in kage.lines if kageline.data[0] == 99]
    if any(part in jv_no_apply_parts for part in used_parts):
        return False  # 簡体字特有の字形
    for part in used_parts:
        if part in jv_no_use_part_replacement:
            # -jvに使わない字形の部品が使用されている
            return [2, part, jv_no_use_part_replacement[part]]
    return False


source_separation = GWGroupLazyLoader("原規格分離")

_re_region_opthenka = re.compile(r"^([gtvhmi]|k[pv]?|us?|j[asv]?)(\d{2})?$")


class Validator(ValidatorClass):

    name = "j"

    def is_invalid(self, name, related, kage, gdata, dump):
        splitname = name.split("-")
        if len(splitname) > 2:
            return False

        if splitname[0] in ("extd", "extf"):
            # TODO: sources of extd, extf- glyphs
            # jsource = cjk_sources.get(name, cjk_sources.COLUMN_J)
            # if jsource is None:
            #     return checkJV(kage)
            return False

        # uXXXX, uXXXX-...
        ucs = splitname[0]
        jsource = cjk_sources.get(ucs, cjk_sources.COLUMN_J)

        if len(splitname) == 1:  # 無印
            if jsource is None and ucs not in jv_no_apply_parts:
                return checkJV(kage)
            return False

        m = _re_region_opthenka.match(splitname[1])
        if not m:
            return False
        region = m.group(1)
        isHenka = m.group(2) is not None

        # Check sources
        if region == "jv":
            if jsource is not None:
                return [30, jsource]  # Jソースがあるのにjv
            if ucs in source_separation.get_data():
                return [5]  # 原規格分離-jv
        elif region == "kv":
            ksource = cjk_sources.get(ucs, cjk_sources.COLUMN_K)
            if ksource is not None:
                return [31, ksource]  # Kソースがあるのにkv
        else:  # not 仮想字形
            if region in ("j", "ja"):
                if jsource is None:
                    return [4]  # ソースが存在しない地域指定
            elif region in cjk_sources.region2index:
                source = cjk_sources.get(ucs, cjk_sources.region2index[region])
                if source is None:
                    return [4]  # ソースが存在しない地域指定
            else:  # -i, -us, -js
                return False

        if region not in ("j", "ja", "jv"):
            return False

        if kage.isAlias():
            entity_name = kage.lines[0].data[7]
        else:
            entity_name = name

        if ucs not in dump:
            return False  # 無印が見つからない
        nomark_kage = KageData(dump[ucs][1])
        if nomark_kage.isAlias():
            nomark_entity_name = nomark_kage.lines[0].data[7]
        else:
            nomark_entity_name = ucs

        if entity_name != nomark_entity_name and not isHenka:
            return [0]  # uxxxx-j, ja, jv (の実体)と無印(の実体)が違う

        if region != "jv":
            return False
        if (ucs + "-j") in dump:
            return [1, "j"]   # uxxxx-jv と uxxxx-j  が共存している
        if (ucs + "-ja") in dump:
            return [1, "ja"]  # uxxxx-jv と uxxxx-ja が共存している
        if ucs not in jv_no_apply_parts:
            if kage.isAlias():
                if entity_name not in dump:
                    return False  # 実体が見つからない
                entity_kage = KageData(dump[entity_name][1])
            else:
                entity_kage = kage
            return checkJV(entity_kage)
        return False
