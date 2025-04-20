from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple

from gwv import filters
from gwv.helper import RE_REGIONS
from gwv.validators import SingleErrorValidator, ValidatorErrorEnum, error_code

if TYPE_CHECKING:
    from gwv.validatorctx import ValidatorContext


class OrderError(NamedTuple):
    part_name: str


class OrderValidatorError(ValidatorErrorEnum):
    @error_code("2")
    class RIGHT_PART_FIRST(OrderError):
        """右部品が最初"""

    @error_code("4")
    class BOTTOM_PART_FIRST(OrderError):
        """下部品が最初"""

    @error_code("6")
    class INNER_PART_FIRST(OrderError):
        """囲み内側部品が最初"""

    @error_code("11")
    class LEFT_PART_LAST(OrderError):
        """左部品が最後"""

    @error_code("13")
    class TOP_PART_LAST(OrderError):
        """上部品が最後"""

    @error_code("15")
    class OUTER_PART_LAST(OrderError):
        """囲み外側部品が最後"""


E = OrderValidatorError


_re_vars = re.compile(r"-" + RE_REGIONS + r"?(\d{2})(-(var|itaiji)-\d{3})?(@|$)")


class OrderValidator(SingleErrorValidator):
    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    @filters.check_only(-filters.has_transform)
    def is_invalid(self, ctx: ValidatorContext):
        if ctx.glyph.kage.len == 1:
            return False
        first = ctx.glyph.kage.lines[0]
        last = ctx.glyph.kage.lines[-1]
        if first.stroke_type == 99:
            fG = first.part_name
            m = _re_vars.search(fG)
            if m:
                henka = m.group(1)
                if henka == "02":
                    return E.RIGHT_PART_FIRST(fG)  # 右部品が最初
                if henka in ("04", "14", "24"):
                    return E.BOTTOM_PART_FIRST(fG)  # 下部品が最初
                if henka == "06":
                    return E.INNER_PART_FIRST(fG)  # 囲み内側部品が最初
        if last.stroke_type == 99:
            lG = last.part_name
            m = _re_vars.search(lG)
            if m:
                henka = m.group(1)
                if henka == "01":
                    return E.LEFT_PART_LAST(lG)  # 左部品が最後
                if henka == "03":
                    return E.TOP_PART_LAST(lG)  # 上部品が最後
                if henka in ("05", "10", "11", "15"):
                    return E.OUTER_PART_LAST(lG)  # 囲み外側部品が最初

        return False
