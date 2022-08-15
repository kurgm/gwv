from typing import NamedTuple, Set

from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class DelquoteValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class PART_NOT_FOUND(NamedTuple):
        """無い部品を引用している"""
        part_name: str


E = DelquoteValidatorError


class DelquoteValidator(Validator):

    def validate(self, ctx: ValidatorContext) -> None:
        error_part_names: Set[str] = set()
        for line in ctx.glyph.kage.lines:
            if line.stroke_type == 99 and \
                    line.part_name.split("@")[0] not in ctx.dump:
                # 無い部品を引用している
                error_part_names.add(line.part_name)
        for error_part_name in error_part_names:
            self.record(ctx.glyph.name, E.PART_NOT_FOUND(error_part_name))
