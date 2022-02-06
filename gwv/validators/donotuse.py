import gwv.filters as filters
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DO_NOT_USE="0",  # do-not-use が引用されている
)


class DonotuseValidator(Validator):

    name = "donotuse"

    @filters.check_only(-filters.is_alias)
    def is_invalid(self, ctx: ValidatorContext):
        quotings = []
        for line in ctx.glyph.kage.lines:
            if line.stroke_type != 99:
                continue
            part_entry = ctx.dump.get(line.part_name.split("@")[0])
            if part_entry and "do-not-use" in part_entry.gdata:
                quotings.append(line.part_name)
        if quotings:
            return [error_codes.DO_NOT_USE] + quotings
        return False
