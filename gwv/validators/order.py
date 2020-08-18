import re

from gwv.helper import RE_REGIONS
from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    RIGHT_PART_FIRST="2",  # 右部品が最初
    BOTTOM_PART_FIRST="4",  # 下部品が最初
    INNER_PART_FIRST="6",  # 囲み内側部品が最初
    LEFT_PART_LAST="11",  # 左部品が最後
    TOP_PART_LAST="13",  # 上部品が最後
    OUTER_PART_LAST="15",  # 囲み外側部品が最後
)


_re_vars = re.compile(
    r"-" + RE_REGIONS + r"?(\d{2})(-(var|itaiji)-\d{3})?(@|$)")


class OrderValidator(Validator):

    name = "order"

    filters = {
        "alias": {False},
        "category": default_filters["category"] - {"user-owned"},
        "transform": {False},
    }

    def is_invalid(self, name, related, kage, gdata, dump):
        if kage.len == 1:
            return False
        first = kage.lines[0]
        last = kage.lines[-1]
        if first.data[0] == 99:
            fG = first.data[7]
            m = _re_vars.search(fG)
            if m:
                henka = m.group(1)
                if henka == "02":
                    return [error_codes.RIGHT_PART_FIRST, fG]  # 右部品が最初
                if henka in ("04", "14", "24"):
                    return [error_codes.BOTTOM_PART_FIRST, fG]  # 下部品が最初
                if henka == "06":
                    return [error_codes.INNER_PART_FIRST, fG]  # 囲み内側部品が最初
        if last.data[0] == 99:
            lG = last.data[7]
            m = _re_vars.search(lG)
            if m:
                henka = m.group(1)
                if henka == "01":
                    return [error_codes.LEFT_PART_LAST, lG]  # 左部品が最後
                if henka == "03":
                    return [error_codes.TOP_PART_LAST, lG]  # 上部品が最後
                if henka in ("05", "10", "11", "15"):
                    return [error_codes.OUTER_PART_LAST, lG]  # 囲み外側部品が最初

        return False
