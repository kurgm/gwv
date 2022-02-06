import re

from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    BLANK_LINE="0",  # 空行
    INVALID_CHAR="1",  # 不正な文字
    NOT_AN_INT="2",  # 整数として解釈できない
    NONNORMALIZED_NUMBER_EXPRESSION="3",  # 不正な数値の表現
)


_re_invalid_chars = re.compile(r"[^\da-z_\:@-]")


class NumexpValidator(Validator):

    name = "numexp"

    def is_invalid(self, ctx: ValidatorContext):
        for i, line in enumerate(ctx.glyph.gdata.split("$")):
            if line == "":
                return [error_codes.BLANK_LINE, [i, line]]  # 空行
            if _re_invalid_chars.search(line):
                return [error_codes.INVALID_CHAR, [i, line]]  # 不正な文字
            data = line.split(":")
            for j, col in enumerate(data):
                if j == 7 and data[0] == "99":
                    continue
                try:
                    numdata = int(col)
                except ValueError:
                    return [error_codes.NOT_AN_INT, [i, line]]  # 整数として解釈できない
                if str(numdata) != col:
                    # 不正な数値の表現
                    return [
                        error_codes.NONNORMALIZED_NUMBER_EXPRESSION, [i, line]]
        return False
