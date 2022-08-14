from typing import Iterable, NamedTuple, Set, Tuple

import gwv.filters as filters
from gwv.helper import isYoko
from gwv.kagedata import KageData, KageLine
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, \
    ValidatorErrorTupleRecorder, error_code


class IllegalLineError(NamedTuple):
    line: KageLine


class IllegalValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class UNKNOWN_STROKE_TYPE(IllegalLineError):
        """未定義の筆画"""
    @error_code("1")
    class TOO_FEW_COLUMNS(IllegalLineError):
        """列不足"""
    @error_code("2")
    class TOO_MANY_NONZERO_COLUMNS(IllegalLineError):
        """列余分（非ゼロ）"""
    @error_code("3")
    class TOO_MANY_ZERO_COLUMNS(IllegalLineError):
        """列余分（ゼロ値）"""
    @error_code("4")
    class WRONG_NUMBER_OF_COLUMNS(IllegalLineError):
        """列数異常（99）"""
    @error_code("5")
    class INVALID_DATA_0(IllegalLineError):
        """不正なデータ（0）"""
    @error_code("6")
    class UNKNOWN_STROKE_FORM(IllegalLineError):
        """未定義の形状の組み合わせ"""
    @error_code("7")
    class ALIAS_LIKE(NamedTuple):
        """正しくエイリアスになっていない"""
    @error_code("8")
    class BLANK_LIKE(NamedTuple):
        """正しく空白グリフになっていない"""

    @error_code("10")
    class VERTCONN_IN_HORI_LINE(IllegalLineError):
        """横画に接続(縦)型"""
    @error_code("11")
    class HORICONN_IN_VERT_LINE(IllegalLineError):
        """縦画に接続(横)型"""
    @error_code("30")
    class HORIZONTAL_ORE_FIRST(IllegalLineError):
        """折れの前半が横"""
    @error_code("31")
    class VERTICAL_ORE_LAST(IllegalLineError):
        """折れの後半が縦"""
    @error_code("40")
    class HORIZONTAL_OTSU_FIRST(IllegalLineError):
        """乙の前半が横"""
    @error_code("41")
    class LEFTWARD_OTSU_LAST(IllegalLineError):
        """乙の後半が左向き"""
    @error_code("9")
    class BUHIN_ICHI(IllegalLineError):
        """部品位置"""


E = IllegalValidatorError


def is_blank_like(kage: KageData):
    for line in kage.lines:
        stype = line.stroke_type
        if stype is None or stype < 0:
            return False
        if stype == 99 or stype % 100 in (1, 2, 3, 4, 6, 7):
            return False
    return True


def is_alias_like(kage: KageData):
    has_200_quote = False
    for line in kage.lines:
        stype = line.stroke_type
        if stype is None or stype < 0:
            return False
        if stype == 0:
            if len(line.data) >= 3 and line.head_type in (97, 98, 99):
                # transform commands
                return False
        elif stype == 99:
            if not (len(line.data) >= 7 and
                    line.coords == [(0, 0), (200, 200)]):
                return False
            sx, sy = line.data[1:3]
            if sx is None or sy is None:
                return False
            if sx > 100:
                sx -= 200
                if len(line.data) < 11:
                    return False
                sx2, sy2 = line.data[9:11]
                if sx2 is None or sy2 is None:
                    return False
            else:
                sx2, sy2 = 0, 0
            if sx == sy == 0 or (sx == sx2 and sy == sy2):
                # stretch has no effect
                if has_200_quote:
                    return False  # multiple 200_quotes
                has_200_quote = True
            else:
                return False
        elif stype % 100 == 9:
            pass
        else:
            return False
    return has_200_quote


keijoKumiawase: Set[Tuple[int, int, int]] = {
    # https://github.com/kurgm/kage-editor/blob/master/src/kageUtils/stroketype.ts
    (1, 0, 0),
    (1, 0, 2),
    (1, 0, 32),
    (1, 0, 13),
    (1, 0, 23),
    (1, 0, 4),
    (1, 0, 313),
    (1, 0, 413),
    (1, 0, 24),
    (1, 2, 0),
    (1, 2, 2),
    (1, 32, 0),
    (1, 32, 32),
    (1, 32, 13),
    (1, 32, 23),
    (1, 32, 4),
    (1, 32, 313),
    (1, 32, 413),
    (1, 32, 24),
    (1, 12, 0),
    (1, 12, 32),
    (1, 12, 13),
    (1, 12, 23),
    (1, 12, 313),
    (1, 12, 413),
    (1, 12, 24),
    (1, 22, 0),
    (1, 22, 32),
    (1, 22, 13),
    (1, 22, 23),
    (1, 22, 4),
    (1, 22, 313),
    (1, 22, 413),
    (1, 22, 24),
    (2, 0, 7),
    (2, 0, 5),
    (2, 32, 7),
    (2, 32, 4),
    (2, 32, 5),
    (2, 12, 7),
    (2, 22, 7),
    (2, 22, 4),
    (2, 22, 5),
    (2, 7, 0),
    (2, 7, 8),
    (2, 7, 4),
    (2, 27, 0),
    (3, 0, 0),
    (3, 0, 5),
    (3, 0, 32),
    (3, 32, 0),
    (3, 32, 5),
    (3, 32, 32),
    (3, 12, 0),
    (3, 12, 5),
    (3, 12, 32),
    (3, 22, 0),
    (3, 22, 5),
    (3, 22, 32),
    (4, 0, 0),
    (4, 0, 5),
    (4, 22, 0),
    (4, 22, 5),
    (6, 0, 7),
    (6, 0, 5),
    (6, 32, 7),
    (6, 32, 4),
    (6, 32, 5),
    (6, 12, 7),
    (6, 22, 7),
    (6, 22, 4),
    (6, 22, 5),
    (6, 7, 0),
    (6, 7, 8),
    (6, 7, 4),
    (6, 27, 0),
    (7, 0, 7),
    (7, 32, 7),
    (7, 12, 7),
    (7, 22, 7),

    (0, 0, 0),
    (0, -1, -1),
    (0, 99, 1),
    (0, 99, 2),
    (0, 99, 3),
    (0, 98, 0),
    (0, 97, 0),
    (9, 0, 0),
}

hikanjiKeijoKumiawase: Set[Tuple[int, int, int]] = keijoKumiawase | {
    (2, 32, 0),  # 曲線、接続→右払い
    (6, 32, 0),  # 複曲線、接続→右払い
    (2, 32, 8),  # 曲線、接続→止め
    (6, 32, 8),  # 複曲線、接続→止め
}

# {筆画タイプ: データ列数}
datalens = {
    1: 7,
    2: 9,
    3: 9,
    4: 9,
    6: 11,
    7: 11,
    9: 7
}


def validate_99_line(ctx: ValidatorContext, line: KageLine):
    data_len = len(line.data)
    if data_len not in (8, 11):
        return E.WRONG_NUMBER_OF_COLUMNS(line)
    return False


def validate_0_line(ctx: ValidatorContext, line: KageLine):
    if line.data in ((0, 0, 0, 0), (0, -1, -1, -1)):
        return False
    if line.data[:3] in (
            (0, 99, 1), (0, 99, 2), (0, 99, 3), (0, 98, 0), (0, 97, 0)):
        if len(line.data) != 7:
            return E.WRONG_NUMBER_OF_COLUMNS(line)
        return False

    if len(line.data) not in (4, 7):
        return E.WRONG_NUMBER_OF_COLUMNS(line)
    if line.data[:3] in ((0, 0, 0), (0, -1, -1)):
        return E.INVALID_DATA_0(line)
    return E.UNKNOWN_STROKE_FORM(line)


def validate_stroke_line(ctx: ValidatorContext, line: KageLine):
    stype = line.stroke_type
    if stype is None:
        return E.UNKNOWN_STROKE_TYPE(line)

    if ctx.is_hikanji and stype >= 0:
        stype %= 100

    if stype not in datalens:
        return E.UNKNOWN_STROKE_TYPE(line)
    expected_len = datalens[stype]
    actual_len = len(line.data)
    if actual_len < expected_len:
        return E.TOO_FEW_COLUMNS(line)
    if actual_len > expected_len:
        if any(n != 0 for n in line.data[expected_len:]):
            return E.TOO_MANY_NONZERO_COLUMNS(line)
        return E.TOO_MANY_ZERO_COLUMNS(line)

    if stype == 9:
        return E.BUHIN_ICHI(line)

    shape0 = line.head_type
    shape1 = line.tail_type
    if shape0 is None or shape1 is None:
        return E.UNKNOWN_STROKE_FORM(line)
    if ctx.is_hikanji:
        if shape0 >= 0:
            shape0 %= 100
        if shape1 >= 0:
            shape1 %= 100

    coords = line.coords
    if coords is not None:
        if stype == 1:
            if isYoko(*coords[0], *coords[1]):
                if shape0 in (12, 22, 32) or \
                        shape1 in (32, 13, 23, 24, 313, 413):
                    return E.VERTCONN_IN_HORI_LINE(line)
            elif shape0 == 2 or shape1 == 2:
                return E.HORICONN_IN_VERT_LINE(line)
        elif stype == 3:
            if isYoko(*coords[0], *coords[1]):
                return E.HORIZONTAL_ORE_FIRST(line)
            if shape1 == 5 and coords[1][0] == coords[2][0]:
                return E.VERTICAL_ORE_LAST(line)
        elif stype == 4:
            if isYoko(*coords[0], *coords[1]):
                return E.HORIZONTAL_OTSU_FIRST(line)
            if shape1 == 5 and coords[1][0] >= coords[2][0]:
                return E.LEFTWARD_OTSU_LAST(line)

    allowed_shape_types = keijoKumiawase
    if ctx.is_hikanji:
        allowed_shape_types = hikanjiKeijoKumiawase
    if (stype, shape0, shape1) not in allowed_shape_types:
        return E.UNKNOWN_STROKE_FORM(line)
    return False


class IllegalValidatorErrorRecorder(ValidatorErrorTupleRecorder):
    def get_result(self):
        for val in self._results.values():
            if val and len(val[0]) >= 3 and type(val[0][1]) is str:
                val.sort(key=lambda r: r[1])
        return super().get_result()


class IllegalValidator(Validator):

    recorder_cls = IllegalValidatorErrorRecorder

    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            stype = line.stroke_type
            if stype == 99:
                if err := validate_99_line(ctx, line):
                    return err
            elif stype == 0:
                if err := validate_0_line(ctx, line):
                    return err
            else:
                if err := validate_stroke_line(ctx, line):
                    return err

        if not ctx.glyph.is_alias and is_alias_like(ctx.glyph.kage):
            return E.ALIAS_LIKE()
        if is_blank_like(ctx.glyph.kage) and ctx.glyph.gdata != "0:-1:-1:-1":
            return E.BLANK_LIKE()
        return False

    def record(self, glyphname: str, error: Tuple[str, Iterable]):
        key, param = error
        if isinstance(param, IllegalLineError):
            super().record(glyphname, (key, (
                ":".join(param.line.strdata.split(":", 3)[:3]),
                *param
            )))
        else:
            super().record(glyphname, error)
