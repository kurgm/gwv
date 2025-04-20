from typing import Any, List, NamedTuple, Tuple

import gwv.filters as filters
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class DonotuseValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class DO_NOT_USE(NamedTuple):
        """do-not-use が引用されている"""

        parts: List[str]


E = DonotuseValidatorError


class DonotuseValidator(Validator):
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
            return E.DO_NOT_USE(quotings)
        return False

    def record(self, glyphname: str, error: Tuple[str, Any]):
        key, param = error
        super().record(glyphname, (key, param.parts))
