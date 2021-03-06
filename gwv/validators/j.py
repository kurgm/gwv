import re
from typing import Dict, Set

from gwv.dump import Dump
import gwv.filters as filters
from gwv.helper import cjk_sources
from gwv.helper import GWGroupLazyLoader
from gwv.helper import load_package_data
from gwv.helper import RE_REGIONS
from gwv.kagedata import KageData
from gwv.validators import ErrorCodes
from gwv.validators import Validator


error_codes = ErrorCodes(
    J_NOMARK_DIFFERENT="0",  # uxxxx-j, ja, jv (の実体)と無印(の実体)が違う
    J_JV_COEXISTENT="1",  # uxxxx-j(a) と jv が共存している
    NONJV_PART="2",  # -jvに使わない字形の部品が使用されている
    JV_HAS_JSOURCE="30",  # Jソースがあるのにjv
    KV_HAS_KSOURCE="31",  # Kソースがあるのにkv
    NO_SOURCE="40",  # ソースが存在しない地域指定
    NO_SOURCE_HENKA="41",  # ソースが存在しない地域指定（偏化変形）
    JV_SOURCE_SEPARATION="5",  # 原規格分離-jv
)


source_separation = GWGroupLazyLoader("原規格分離", isset=True)

_re_region_opthenka = re.compile(r"^(" + RE_REGIONS + r")(\d{2})?$")


class JValidator(Validator):

    name = "j"

    def __init__(self):
        Validator.__init__(self)
        self.jv_no_use_part_replacement: Dict[str, str] = {}
        self.jv_no_apply_parts: Set[str] = set()

    def setup(self, dump: Dump):
        jv_data = load_package_data("data/jv.yaml")
        self.jv_no_use_part_replacement = {
            no_use_alias: use
            for use, no_uses in jv_data["no-use-part"].items()
            for no_use in no_uses
            for no_use_alias in dump.get_alias_of(no_use)
        }
        re_no_apply_jv = re.compile(
            r"(" + r"|".join(jv_data["no-apply-jv"]) +
            r")(-(" + RE_REGIONS + r")(\d{2})?$|(-\d{2})?(-var-\d{3})?)$")
        self.jv_no_apply_parts = {
            part_alias
            for part in dump if re_no_apply_jv.match(part)
            for part_alias in dump.get_alias_of(part)
        }

    def checkJV(self, kage: KageData):
        used_parts = [kageline.part_name.split("@")[0]
                      for kageline in kage.lines if kageline.stroke_type == 99]
        if any(part in self.jv_no_apply_parts for part in used_parts):
            return False  # 簡体字特有の字形
        for part in used_parts:
            if part in self.jv_no_use_part_replacement:
                # -jvに使わない字形の部品が使用されている
                return [
                    error_codes.NONJV_PART,
                    part, self.jv_no_use_part_replacement[part]
                ]
        return False

    @filters.check_only(+filters.is_of_category({
        "togo", "togo-var", "gokan-var", "ext", "bsh"}))
    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        splitname = name.split("-")

        if len(splitname) == 3 and splitname[:2] == ["unstable", "bsh"]:
            return self.checkJV(kage.get_entity(dump))

        if len(splitname) > 2:
            return False

        if splitname[0] in ("irg2015", "irg2017"):
            # irg2015-, irg2017- glyphs have no J source
            return self.checkJV(kage.get_entity(dump))

        # uXXXX, uXXXX-...
        ucs = splitname[0]
        jsource = cjk_sources.get(ucs, cjk_sources.COLUMN_J)

        if len(splitname) == 1:  # 無印
            if jsource is None and ucs not in self.jv_no_apply_parts and \
                    ucs not in source_separation.get_data():
                return self.checkJV(kage.get_entity(dump))
            return False

        m = _re_region_opthenka.match(splitname[1])
        if not m:
            return False
        region = m.group(1)
        isHenka = m.group(2) is not None

        # Check sources
        if region == "jv":
            if jsource is not None:
                return [error_codes.JV_HAS_JSOURCE, jsource]  # Jソースがあるのにjv
            if ucs in source_separation.get_data():
                return [error_codes.JV_SOURCE_SEPARATION]  # 原規格分離-jv
        elif region == "kv":
            ksource = cjk_sources.get(ucs, cjk_sources.COLUMN_K)
            if ksource is not None:
                return [error_codes.KV_HAS_KSOURCE, ksource]  # Kソースがあるのにkv
        elif region in ("gv", "tv", "vv"):
            # TODO
            return False
        else:  # not 仮想字形
            if region in ("j", "ja"):
                if jsource is None:
                    # ソースが存在しない地域指定
                    return [error_codes.NO_SOURCE_HENKA
                            if isHenka else error_codes.NO_SOURCE]
            elif region in cjk_sources.region2index:
                source = cjk_sources.get(ucs, cjk_sources.region2index[region])
                if source is None:
                    # ソースが存在しない地域指定
                    return [error_codes.NO_SOURCE_HENKA
                            if isHenka else error_codes.NO_SOURCE]
            else:  # -i, -us, -js
                return False

        if region not in ("j", "ja", "jv"):
            return False

        if kage.is_alias:
            entity_name = kage.lines[0].part_name
        else:
            entity_name = name

        if ucs not in dump:
            return False  # 無印が見つからない
        nomark_kage = KageData(dump[ucs][1])
        if nomark_kage.is_alias:
            nomark_entity_name = nomark_kage.lines[0].part_name
        else:
            nomark_entity_name = ucs

        if entity_name != nomark_entity_name and not isHenka:
            # uxxxx-j, ja, jv (の実体)と無印(の実体)が違う
            return [error_codes.J_NOMARK_DIFFERENT]

        if region != "jv":
            return False
        if (ucs + "-j") in dump:
            # uxxxx-jv と uxxxx-j  が共存している
            return [error_codes.J_JV_COEXISTENT, "j"]
        if (ucs + "-ja") in dump:
            # uxxxx-jv と uxxxx-ja が共存している
            return [error_codes.J_JV_COEXISTENT, "ja"]
        if ucs not in self.jv_no_apply_parts:
            return self.checkJV(kage.get_entity(dump))
        return False
