from gwv.dump import Dump, DumpEntry
import gwv.filters as filters
from gwv.helper import cjk_sources
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    WRONG_RELATED="0",  # 間違った関連字
    MISSING_RELATED="1",  # 関連字なし
    ENTITY_NOT_FOUND="2",  # 実体が存在しない
    WRONG_ENTITY_RELATED="10",  # 実体の関連字が違う
    MISSING_ENTITY_RELATED="11",  # 実体が関連字なし
)


class RelatedValidator(Validator):

    name = "related"

    @filters.check_only(+filters.is_of_category({
        "togo", "togo-var", "gokan", "gokan-var"}))
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        expected_related = entry.name.split("-")[0]
        if isGokanKanji(expected_related):
            u = cjk_sources.get(
                expected_related, cjk_sources.COLUMN_COMPATIBILITY_VARIANT)
            if u is None:
                return False
            expected_related = "u" + u[2:].lower()

        if entry.related != "u3013" and expected_related != entry.related:
            # 間違った関連字
            return [error_codes.WRONG_RELATED, entry.related, expected_related]

        if entry.entity_name is not None:
            entity_header = entry.entity_name.split("-")[0]
            if isTogoKanji(entity_header):
                return False
            if entry.entity_name not in dump:
                # 実体が存在しない
                return [error_codes.ENTITY_NOT_FOUND, entry.entity_name]

            related = dump[entry.entity_name].related
            if related == "u3013":
                # 実体が関連字なし
                return [
                    error_codes.MISSING_ENTITY_RELATED,
                    entry.entity_name, expected_related]

            if expected_related != related:
                # 実体の関連字が違う
                return [
                    error_codes.WRONG_ENTITY_RELATED,
                    entry.entity_name, related, expected_related]

        elif entry.related == "u3013":
            return [error_codes.MISSING_RELATED, expected_related]  # 関連字なし

        return False
