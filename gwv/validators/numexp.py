import re
from typing import NamedTuple, Tuple

from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class NumexpError(NamedTuple):
    line: Tuple[int, str]  # kage line number and daata


class NumexpValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class BLANK_LINE(NumexpError):
        """空行"""
    @error_code("1")
    class INVALID_CHAR(NumexpError):
        """不正な文字"""
    @error_code("2")
    class NOT_AN_INT(NumexpError):
        """整数として解釈できない"""
    @error_code("3")
    class NONNORMALIZED_NUMBER_EXPRESSION(NumexpError):
        """不正な数値の表現"""


E = NumexpValidatorError


_re_invalid_chars = re.compile(r"[^\da-z_\:@-]")


class NumexpValidator(Validator):

    def is_invalid(self, ctx: ValidatorContext):
        for i, line in enumerate(ctx.glyph.gdata.split("$")):
            if line == "":
                return E.BLANK_LINE((i, line))  # 空行
            if _re_invalid_chars.search(line):
                return E.INVALID_CHAR((i, line))  # 不正な文字
            data = line.split(":")
            for j, col in enumerate(data):
                if j == 7 and data[0] == "99":
                    continue
                try:
                    numdata = int(col)
                except ValueError:
                    return E.NOT_AN_INT((i, line))  # 整数として解釈できない
                if str(numdata) != col:
                    # 不正な数値の表現
                    return E.NONNORMALIZED_NUMBER_EXPRESSION((i, line))
        return False
