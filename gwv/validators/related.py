import gwv.filters as filters
from gwv.helper import categorize, cjk_sources, is_gokan_kanji_cp, \
    is_togo_kanji_cp
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

    @filters.check_only(+filters.is_of_category({"ucs-kanji"}))
    def is_invalid(self, ctx: ValidatorContext):
        expected_related = "u" + ctx.category_param[1][0]
        if is_gokan_kanji_cp(int(expected_related[1:], 16)):
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
            entity_category, entity_param = categorize(ctx.glyph.entity_name)
            if entity_category == "ucs-kanji" and \
                    is_togo_kanji_cp(int(entity_param[0], 16)):
                return False
            if ctx.glyph.entity_name not in ctx.dump:
                # 実体が存在しない
                return [error_codes.ENTITY_NOT_FOUND, ctx.glyph.entity_name]

            related = ctx.entity.related
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
