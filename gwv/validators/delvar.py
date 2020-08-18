import re

from gwv.dump import Dump
from gwv.helper import RE_REGIONS
from gwv.kagedata import KageData
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    BASE_NOT_FOUND="0",  # 派生元が無い
)


_re_var_nnn_henka = re.compile(r"^(.+)-((var|itaiji)-\d{3}|\d{2})$")
_re_var_src_henka = re.compile(
    r"^(u[0-9a-f]{4,5}-" + RE_REGIONS + r")(\d{2})$")
_re_var_other = re.compile(r"^(u[0-9a-f]{4,5}|cdp[on]?-[0-9a-f]{4})-")


class DelvarValidator(Validator):

    name = "delvar"

    filters = {
        "category": {
            "ids", "togo-var", "gokan-var", "ucs-hikanji-var", "cdp", "other"}
    }

    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        m = _re_var_nnn_henka.match(name) or _re_var_src_henka.match(name) or \
            _re_var_other.match(name)
        if m:
            prefix = m.group(1)
            if prefix not in dump:
                return [error_codes.BASE_NOT_FOUND, prefix]  # 派生元が無い
        return None
