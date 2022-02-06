import gwv.filters as filters
from gwv.helper import cjk_sources
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.validatorctx import ValidatorContext
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
    def is_invalid(self, ctx: ValidatorContext):
        expected_related = ctx.glyph.name.split("-")[0]
        if isGokanKanji(expected_related):
            u = cjk_sources.get(
                expected_related, cjk_sources.COLUMN_COMPATIBILITY_VARIANT)
            if u is None:
                return False
            expected_related = "u" + u[2:].lower()

        if ctx.glyph.related != "u3013" and \
                expected_related != ctx.glyph.related:
            # 間違った関連字
            return [
                error_codes.WRONG_RELATED, ctx.glyph.related, expected_related]

        if ctx.glyph.entity_name is not None:
            entity_header = ctx.glyph.entity_name.split("-")[0]
            if isTogoKanji(entity_header):
                return False
            if ctx.glyph.entity_name not in ctx.dump:
                # 実体が存在しない
                return [error_codes.ENTITY_NOT_FOUND, ctx.glyph.entity_name]

            related = ctx.dump[ctx.glyph.entity_name].related
            if related == "u3013":
                # 実体が関連字なし
                return [
                    error_codes.MISSING_ENTITY_RELATED,
                    ctx.glyph.entity_name, expected_related]

            if expected_related != related:
                # 実体の関連字が違う
                return [
                    error_codes.WRONG_ENTITY_RELATED,
                    ctx.glyph.entity_name, related, expected_related]

        elif ctx.glyph.related == "u3013":
            return [error_codes.MISSING_RELATED, expected_related]  # 関連字なし

        return False
