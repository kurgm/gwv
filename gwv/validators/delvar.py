import re
from typing import NamedTuple

import gwv.filters as filters
from gwv.helper import RE_REGIONS
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class DelvarValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class BASE_NOT_FOUND(NamedTuple):
        """派生元が無い"""
        base: str


E = DelvarValidatorError


_re_var_nnn_henka = re.compile(r"(.+)-(?:(?:var|itaiji)-\d{3}|\d{2})")
_re_var_src_henka = re.compile(r"(u[0-9a-f]{4,5}-" + RE_REGIONS + r")\d{2}")
_re_var_other = re.compile(r"(u[0-9a-f]{4,5}|cdp[on]?-[0-9a-f]{4})-.+")


class DelvarValidator(Validator):

    @filters.check_only(-filters.is_of_category({
        "user-owned", "koseki", "toki", "ext", "bsh"}))
    def is_invalid(self, ctx: ValidatorContext):
        m = _re_var_nnn_henka.fullmatch(ctx.glyph.name) or \
            _re_var_src_henka.fullmatch(ctx.glyph.name) or \
            _re_var_other.fullmatch(ctx.glyph.name)
        if m:
            prefix = m.group(1)
            if prefix not in ctx.dump:
                return E.BASE_NOT_FOUND(prefix)  # 派生元が無い
        return None
