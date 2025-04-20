from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from gwv import filters
from gwv.validators import SingleErrorValidator, ValidatorErrorEnum, error_code

if TYPE_CHECKING:
    from gwv.validatorctx import ValidatorContext


class KosekitokiValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class NOT_ALIAS(NamedTuple):
        """エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）"""

    @error_code("1")
    class NOT_ALIAS_OF_KOSEKI(NamedTuple):
        """koseki-xxxxx0のエイリアスでない"""

        entity: str

    @error_code("2")
    class NOT_ALIAS_OF_ENTITY_OF_KOSEKI(NamedTuple):
        """koseki-xxxxx0と異なる実体のエイリアス"""

        entity: str
        koseki_entity: str


E = KosekitokiValidatorError


class KosekitokiValidator(SingleErrorValidator):
    @filters.check_only(+filters.is_of_category({"toki"}))
    def is_invalid(self, ctx: ValidatorContext):
        (num,) = ctx.category_param[1]
        if not num.startswith("00"):
            return False

        koseki_name = "koseki-" + num[2:]
        if koseki_name in ctx.dump:
            koseki_entity = ctx.dump.get_entity_name(koseki_name)
        else:
            koseki_entity = koseki_name

        entity = ctx.entity.name
        if entity != koseki_entity:
            if not ctx.glyph.is_alias:
                # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
                return E.NOT_ALIAS()
            if koseki_entity == koseki_name:
                # koseki-xxxxx0のエイリアスでない
                return E.NOT_ALIAS_OF_KOSEKI(entity)
            # koseki-xxxxx0と異なる実体のエイリアス
            return E.NOT_ALIAS_OF_ENTITY_OF_KOSEKI(entity, koseki_entity)
        return False
