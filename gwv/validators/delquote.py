from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    PART_NOT_FOUND="0",  # 無い部品を引用している
)


class DelquoteValidator(Validator):


    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            if line.stroke_type == 99 and \
                    line.part_name.split("@")[0] not in ctx.dump:
                # 無い部品を引用している
                return [error_codes.PART_NOT_FOUND, line.part_name]
        return False
