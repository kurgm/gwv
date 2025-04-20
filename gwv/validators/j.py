import re
from typing import Dict, Literal, NamedTuple, Set

from gwv.dump import Dump
import gwv.filters as filters
from gwv.helper import cjk_sources, is_gokan_kanji_cp
from gwv.helper import GWGroupLazyLoader
from gwv.helper import load_package_data
from gwv.helper import RE_REGIONS
from gwv.kagedata import KageData
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class JValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class J_NOMARK_DIFFERENT(NamedTuple):
        """uxxxx-j, ja, jv (の実体)と無印(の実体)が違う"""

    @error_code("1")
    class J_JV_COEXISTENT(NamedTuple):
        """uxxxx-j(a) と jv が共存している"""

        j_or_ja: Literal["j", "ja"]

    @error_code("2")
    class NONJV_PART(NamedTuple):
        """-jvに使わない字形の部品が使用されている"""

        banned_part: str
        preferred_part: str

    @error_code("30")
    class JV_HAS_JSOURCE(NamedTuple):
        """Jソースがあるのにjv"""

        source: str

    @error_code("31")
    class KV_HAS_KSOURCE(NamedTuple):
        """Kソースがあるのにkv"""

        source: str

    @error_code("40")
    class NO_SOURCE(NamedTuple):
        """ソースが存在しない地域指定"""

    @error_code("41")
    class NO_SOURCE_HENKA(NamedTuple):
        """ソースが存在しない地域指定（偏化変形）"""

    @error_code("5")
    class JV_SOURCE_SEPARATION(NamedTuple):
        """原規格分離-jv"""


E = JValidatorError


source_separation = GWGroupLazyLoader("原規格分離", isset=True)

_re_region_opthenka = re.compile(r"-(" + RE_REGIONS + r")(\d{2})?")


class JValidator(Validator):
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
            r"("
            + r"|".join(jv_data["no-apply-jv"])
            + r")(-("
            + RE_REGIONS
            + r")(\d{2})?$|(-\d{2})?(-var-\d{3})?)$"
        )
        self.jv_no_apply_parts = {
            part_alias
            for part in dump
            if re_no_apply_jv.match(part)
            for part_alias in dump.get_alias_of(part)
        }

    def checkJV(self, kage: KageData):
        used_parts = [
            kageline.part_name.split("@")[0]
            for kageline in kage.lines
            if kageline.stroke_type == 99
        ]
        if any(part in self.jv_no_apply_parts for part in used_parts):
            return False  # 簡体字特有の字形
        for part in used_parts:
            if part in self.jv_no_use_part_replacement:
                # -jvに使わない字形の部品が使用されている
                return E.NONJV_PART(part, self.jv_no_use_part_replacement[part])
        return False

    @filters.check_only(+filters.is_of_category({"ucs-kanji", "ext", "bsh"}))
    def is_invalid(self, ctx: ValidatorContext):
        if ctx.category in ("bsh", "ext"):
            # irg2015-, irg2017-, irg2021- glyphs have no J source
            return self.checkJV(ctx.entity.kage)

        # uXXXX, uXXXX-...
        ucs, tail = ctx.category_param[1]
        ucs = "u" + ucs
        jsource = cjk_sources.get(ucs, cjk_sources.COLUMN_J)

        if tail == "":  # 無印
            if is_gokan_kanji_cp(int(ucs[1:], 16)):
                return False
            if (
                jsource is None
                and ucs not in self.jv_no_apply_parts
                and ucs not in source_separation.get_data()
            ):
                return self.checkJV(ctx.entity.kage)
            return False

        m = _re_region_opthenka.fullmatch(tail)
        if not m:
            return False
        region = m.group(1)
        isHenka = m.group(2) is not None

        # Check sources
        if region == "jv":
            if jsource is not None:
                return E.JV_HAS_JSOURCE(jsource)  # Jソースがあるのにjv
            if ucs in source_separation.get_data():
                return E.JV_SOURCE_SEPARATION()  # 原規格分離-jv
        elif region == "kv":
            ksource = cjk_sources.get(ucs, cjk_sources.COLUMN_K)
            if ksource is not None:
                return E.KV_HAS_KSOURCE(ksource)  # Kソースがあるのにkv
        elif region in ("gv", "tv", "vv", "hv"):
            # TODO
            return False
        elif region == "jn":
            # TODO
            return False
        else:  # not 仮想字形
            if region in ("j", "ja"):
                if jsource is None:
                    # ソースが存在しない地域指定
                    return E.NO_SOURCE_HENKA() if isHenka else E.NO_SOURCE()
            elif region in cjk_sources.region2index:
                source = cjk_sources.get(ucs, cjk_sources.region2index[region])
                if source is None:
                    # ソースが存在しない地域指定
                    return E.NO_SOURCE_HENKA() if isHenka else E.NO_SOURCE()
            else:  # -i, -us, -js
                return False

        if region not in ("j", "ja", "jv"):
            return False

        entity_name = ctx.entity.name

        if ucs not in ctx.dump:
            return False  # 無印が見つからない
        nomark_entity_name = ctx.dump.get_entity_name(ucs)

        if entity_name != nomark_entity_name and not isHenka:
            # uxxxx-j, ja, jv (の実体)と無印(の実体)が違う
            return E.J_NOMARK_DIFFERENT()

        if region != "jv":
            return False
        if (ucs + "-j") in ctx.dump:
            # uxxxx-jv と uxxxx-j  が共存している
            return E.J_JV_COEXISTENT("j")
        if (ucs + "-ja") in ctx.dump:
            # uxxxx-jv と uxxxx-ja が共存している
            return E.J_JV_COEXISTENT("ja")
        if ucs not in self.jv_no_apply_parts:
            return self.checkJV(ctx.entity.kage)
        return False
