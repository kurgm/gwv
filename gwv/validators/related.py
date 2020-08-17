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

filters = {
    "alias": {True, False},
    "category": {"togo", "togo-var", "gokan", "gokan-var"}
}


class RelatedValidator(Validator):

    name = "related"

    def is_invalid(self, name, related, kage, gdata, dump):
        expected_related = name.split("-")[0]
        if isGokanKanji(expected_related):
            u = cjk_sources.get(
                expected_related, cjk_sources.COLUMN_COMPATIBILITY_VARIANT)
            if u is None:
                return False
            expected_related = "u" + u[2:].lower()

        if related != "u3013" and expected_related != related:
            return [error_codes.WRONG_RELATED, related, expected_related]  # 間違った関連字

        if kage.isAlias():
            entity_name = gdata[19:]
            entity_header = entity_name.split("-")[0]
            if isTogoKanji(entity_header):
                return False
            if entity_name not in dump:
                return [error_codes.ENTITY_NOT_FOUND, entity_name]  # 実体が存在しない

            related = dump[entity_name][0]
            if related == "u3013":
                # 実体が関連字なし
                return [error_codes.MISSING_ENTITY_RELATED, entity_name, expected_related]

            if expected_related != related:
                # 実体の関連字が違う
                return [error_codes.WRONG_ENTITY_RELATED, entity_name, related, expected_related]

        elif related == "u3013":
            return [error_codes.MISSING_RELATED, expected_related]  # 関連字なし

        return False


validator_class = RelatedValidator
