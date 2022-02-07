import re

import gwv.filters as filters
from gwv.helper import RE_REGIONS
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    BASE_NOT_FOUND="0",  # 派生元が無い
)


_re_var_nnn_henka = re.compile(r"(.+)-(?:(?:var|itaiji)-\d{3}|\d{2})")
_re_var_src_henka = re.compile(r"(u[0-9a-f]{4,5}-" + RE_REGIONS + r")\d{2}")
_re_var_other = re.compile(r"(u[0-9a-f]{4,5}|cdp[on]?-[0-9a-f]{4})-.+")


class DelvarValidator(Validator):

    name = "delvar"

    @filters.check_only(-filters.is_of_category({
        "user-owned", "koseki", "toki", "ext", "bsh"}))
    def is_invalid(self, ctx: ValidatorContext):
        m = _re_var_nnn_henka.fullmatch(ctx.glyph.name) or \
            _re_var_src_henka.fullmatch(ctx.glyph.name) or \
            _re_var_other.fullmatch(ctx.glyph.name)
        if m:
            prefix = m.group(1)
            if prefix not in ctx.dump:
                return [error_codes.BASE_NOT_FOUND, prefix]  # 派生元が無い
        return None
