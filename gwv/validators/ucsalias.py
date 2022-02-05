import re

from gwv.dump import Dump, DumpEntry
import gwv.filters as filters
from gwv.helper import RE_REGIONS
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    VAR_HAS_SAME_ENTITY_AS_NOMARK="10",  # uxxxx-var-xxx が uxxxx (の実体)の別名
    ITAIJI_HAS_SAME_ENTITY_AS_NOMARK="20",  # uxxxx-itaiji-xxx が uxxxx (の実体)の別名
    REGION_IS_ALIAS_OF_NOMARK="1",  # 地域ソース字形が無印のエイリアス
    UCS_IS_ALIAS_OF_NON_UCS="0",  # “uxxxx”が“uyyyy-…”以外やIDSのエイリアス
    UCS_IS_ALIAS_OF_VAR="11",  # uxxxx が uxxxx-var-xxx の別名
    UCS_IS_ALIAS_OF_ITAIJI="21",  # uxxxx が uxxxx-itaiji-xxx の別名
)

_re_sources = re.compile(RE_REGIONS)
_re_ucs_ = re.compile(r"u[\da-f]+(-|$)")
_re_ids = re.compile(r"u2ff.-")


class UcsaliasValidator(Validator):

    name = "ucsalias"

    @filters.check_only(+filters.is_alias)
    @filters.check_only(+filters.is_of_category({
        "togo", "togo-var", "gokan", "gokan-var", "ucs-hikanji",
        "ucs-hikanji-var"}))
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        entity: str = entry.entity_name
        if "-" in entry.name:
            sname = entry.name.split("-")
            len_sname = len(sname)
            if len_sname > 3:
                return False
            if len_sname == 3:
                if sname[1] not in ("var", "itaiji"):
                    return False
                if sname[0] not in dump:
                    return False  # 無印が見つからない
                nomark_entity = dump.get_entity_name(sname[0])
                if sname[1] == "var":
                    # uxxxx-var-xxx が uxxxx (の実体)の別名
                    return [error_codes.VAR_HAS_SAME_ENTITY_AS_NOMARK, entity]\
                        if entity == nomark_entity else False
                # uxxxx-itaiji-xxx が uxxxx (の実体)の別名
                return [error_codes.ITAIJI_HAS_SAME_ENTITY_AS_NOMARK, entity] \
                    if entity == nomark_entity else False
            if _re_sources.fullmatch(sname[1]):
                return [error_codes.REGION_IS_ALIAS_OF_NOMARK] \
                    if entity == sname[0] else False
            return False
        if not _re_ucs_.match(entity) or _re_ids.match(entity):
            if entity == "undefined":
                return False
            # “uxxxx”が“uyyyy-…”以外やIDSのエイリアス
            return [error_codes.UCS_IS_ALIAS_OF_NON_UCS, entity]
        s_entity = entity.split("-")
        if s_entity[0] == entry.name and len(s_entity) == 3:
            if s_entity[1] == "var":
                # uxxxx が uxxxx-var-xxx の別名
                return [error_codes.UCS_IS_ALIAS_OF_VAR, entity]
            if s_entity[1] == "itaiji":
                # uxxxx が uxxxx-itaiji-xxx の別名
                return [error_codes.UCS_IS_ALIAS_OF_ITAIJI, entity]
        return False
