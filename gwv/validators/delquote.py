from typing import NamedTuple

from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class DelquoteValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class PART_NOT_FOUND(NamedTuple):
        """無い部品を引用している"""
        part_name: str


E = DelquoteValidatorError


class DelquoteValidator(Validator):

    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            if line.stroke_type == 99 and \
                    line.part_name.split("@")[0] not in ctx.dump:
                # 無い部品を引用している
                return E.PART_NOT_FOUND(line.part_name)
        return False
