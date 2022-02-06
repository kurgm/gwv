import gwv.filters as filters
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    NOT_ALIAS="0",  # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
    NOT_ALIAS_OF_KOSEKI="1",  # koseki-xxxxx0のエイリアスでない
    NOT_ALIAS_OF_ENTITY_OF_KOSEKI="2",  # koseki-xxxxx0と異なる実体のエイリアス
)


class KosekitokiValidator(Validator):

    name = "kosekitoki"

    @filters.check_only(+filters.is_of_category({"toki"}))
    def is_invalid(self, ctx: ValidatorContext):
        header = ctx.glyph.name[:7]
        if header != "toki-00":
            return False

        koseki_name = "koseki-" + ctx.glyph.name[7:]
        if koseki_name in ctx.dump:
            koseki_entity = ctx.dump.get_entity_name(koseki_name)
        else:
            koseki_entity = koseki_name

        entity = ctx.entity.name
        if entity != koseki_entity:
            if not ctx.glyph.is_alias:
                # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
                return [error_codes.NOT_ALIAS]
            if koseki_entity == koseki_name:
                # koseki-xxxxx0のエイリアスでない
                return [error_codes.NOT_ALIAS_OF_KOSEKI, entity]
            # koseki-xxxxx0と異なる実体のエイリアス
            return [
                error_codes.NOT_ALIAS_OF_ENTITY_OF_KOSEKI,
                entity, koseki_entity]
        return False
