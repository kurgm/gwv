import re
from typing import NamedTuple

import gwv.filters as filters
from gwv.helper import RE_REGIONS
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class UcsaliasError(NamedTuple):
    entity: str


class UcsaliasValidatorError(ValidatorErrorEnum):
    @error_code("10")
    class VAR_HAS_SAME_ENTITY_AS_NOMARK(UcsaliasError):
        """uxxxx-var-xxx が uxxxx (の実体)の別名"""

    @error_code("20")
    class ITAIJI_HAS_SAME_ENTITY_AS_NOMARK(UcsaliasError):
        """uxxxx-itaiji-xxx が uxxxx (の実体)の別名"""

    @error_code("1")
    class REGION_IS_ALIAS_OF_NOMARK(NamedTuple):
        """地域ソース字形が無印のエイリアス"""

    @error_code("0")
    class UCS_IS_ALIAS_OF_NON_UCS(UcsaliasError):
        """“uxxxx”が“uyyyy-…”以外やIDSのエイリアス"""

    @error_code("11")
    class UCS_IS_ALIAS_OF_VAR(UcsaliasError):
        """uxxxx が uxxxx-var-xxx の別名"""

    @error_code("21")
    class UCS_IS_ALIAS_OF_ITAIJI(UcsaliasError):
        """uxxxx が uxxxx-itaiji-xxx の別名"""


E = UcsaliasValidatorError


_re_sources = re.compile(r"-" + RE_REGIONS)
_re_tail_var_itaiji = re.compile(r"-(var|itaiji)-\d{3}")
_re_ucs_ = re.compile(r"u[\da-f]+(-|$)")
_re_ids = re.compile(r"(u2ff[\da-f]|u31ef)-")


class UcsaliasValidator(Validator):
    @filters.check_only(+filters.is_alias)
    @filters.check_only(+filters.is_of_category({"ucs-kanji", "ucs-hikanji"}))
    def is_invalid(self, ctx: ValidatorContext):
        entity: str = ctx.glyph.entity_name  # type: ignore
        name_cp, name_tail = ctx.category_param[1]
        nomark = "u" + name_cp
        if name_tail:
            m = _re_tail_var_itaiji.fullmatch(name_tail)
            if m:
                var_or_itaiji = m.group(1)
                if nomark not in ctx.dump:
                    return False  # 無印が見つからない
                nomark_entity = ctx.dump.get_entity_name(nomark)
                if var_or_itaiji == "var":
                    # uxxxx-var-xxx が uxxxx (の実体)の別名
                    return (
                        E.VAR_HAS_SAME_ENTITY_AS_NOMARK(entity)
                        if entity == nomark_entity
                        else False
                    )
                # uxxxx-itaiji-xxx が uxxxx (の実体)の別名
                return (
                    E.ITAIJI_HAS_SAME_ENTITY_AS_NOMARK(entity)
                    if entity == nomark_entity
                    else False
                )
            if _re_sources.fullmatch(name_tail):
                return E.REGION_IS_ALIAS_OF_NOMARK() if entity == nomark else False
            return False
        if not _re_ucs_.match(entity) or _re_ids.match(entity):
            if entity == "undefined":
                return False
            # “uxxxx”が“uyyyy-…”以外やIDSのエイリアス
            return E.UCS_IS_ALIAS_OF_NON_UCS(entity)

        if entity.startswith(nomark + "-") and (
            m := _re_tail_var_itaiji.fullmatch(entity, len(nomark))
        ):
            var_or_itaiji = m.group(1)
            if var_or_itaiji == "var":
                # uxxxx が uxxxx-var-xxx の別名
                return E.UCS_IS_ALIAS_OF_VAR(entity)
            # uxxxx が uxxxx-itaiji-xxx の別名
            return E.UCS_IS_ALIAS_OF_ITAIJI(entity)
        return False
