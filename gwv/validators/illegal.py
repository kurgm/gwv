from typing import NamedTuple

import gwv.filters as filters
from gwv.helper import isYoko
from gwv.kagedata import KageLine
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class IllegalError(NamedTuple):
    line: KageLine


class IllegalValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class UNKNOWN_STROKE_TYPE(IllegalError):
        """未定義の筆画"""
    @error_code("1")
    class TOO_FEW_COLUMNS(IllegalError):
        """列不足"""
    @error_code("2")
    class TOO_MANY_NONZERO_COLUMNS(IllegalError):
        """列余分（非ゼロ）"""
    @error_code("3")
    class TOO_MANY_ZERO_COLUMNS(IllegalError):
        """列余分（ゼロ値）"""
    @error_code("4")
    class WRONG_NUMBER_OF_COLUMNS(IllegalError):
        """列数異常（99）"""
    @error_code("5")
    class INVALID_DATA_0(IllegalError):
        """不正なデータ（0）"""
    @error_code("6")
    class UNKNOWN_STROKE_FORM(IllegalError):
        """未定義の形状の組み合わせ"""
    @error_code("7")
    class ALIAS_11_COLUMNS(IllegalError):
        """エイリアスに11列"""

    @error_code("10")
    class VERTCONN_IN_HORI_LINE(IllegalError):
        """横画に接続(縦)型"""
    @error_code("11")
    class HORICONN_IN_VERT_LINE(IllegalError):
        """縦画に接続(横)型"""
    @error_code("30")
    class HORIZONTAL_ORE_FIRST(IllegalError):
        """折れの前半が横"""
    @error_code("31")
    class VERTICAL_ORE_LAST(IllegalError):
        """折れの後半が縦"""
    @error_code("40")
    class HORIZONTAL_OTSU_FIRST(IllegalError):
        """乙の前半が横"""
    @error_code("41")
    class LEFTWARD_OTSU_LAST(IllegalError):
        """乙の後半が左向き"""
    @error_code("9")
    class BUHIN_ICHI(IllegalError):
        """部品位置"""


E = IllegalValidatorError


keijoKumiawase = {
    tuple([int(x) for x in keijoStr.split(":")])
    for keijoStr in (
        "0:0:0,0:-1:-1,0:99:1,0:99:2,0:99:3,0:98:0,0:97:0,"

        "1:0:0,1:0:13,1:0:2,1:0:23,1:0:24,1:0:313,1:0:32,1:0:4,1:12:0,1:12:13,"
        "1:12:23,1:12:24,1:12:313,1:12:32,1:12:413,1:2:0,1:2:2,1:22:0,1:22:13,"
        "1:22:23,1:22:24,1:22:313,1:22:32,1:22:4,1:22:413,1:32:0,1:32:13,"
        "1:32:23,1:32:24,1:32:313,1:32:32,1:32:4,1:32:413,"

        "2:0:5,2:0:7,2:12:7,2:22:4,2:22:5,2:22:7,2:32:4,2:32:5,2:32:7,2:7:0,"
        "2:7:4,2:7:8,"

        "3:0:0,3:0:5,3:12:0,3:12:5,3:22:5,3:32:0,3:32:5,"

        "4:0:0,4:0:5,4:22:0,4:22:5,"

        "6:0:5,6:0:7,6:12:7,6:22:4,6:22:5,6:22:7,6:32:4,6:32:5,6:32:7,6:7:0,"
        "6:7:4,6:7:8,"

        "7:0:7,7:12:7,7:32:7,"

        "9:0:0"

        ",7:22:7,3:22:0,1:0:413"  # グリフエディタではエラーになるが……
        ",2:27:0,6:27:0"  # 屋根付き細入り
    ).split(",")
}

hikanjiKeijoKumiawase = {
    tuple([int(x) for x in keijoStr.split(":")])
    for keijoStr in [
        "2:32:0",  # 曲線、接続→右払い
        "6:32:0",  # 複曲線、接続→右払い
        "2:32:8",  # 曲線、接続→止め
        "6:32:8"   # 複曲線、接続→止め
    ]
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


class IllegalValidator(Validator):

    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            lendata = len(line.data)
            stype = line.stroke_type
            try:
                sttType = line.head_type
            except IndexError:
                sttType = 0
            try:
                endType = line.tail_type
            except IndexError:
                endType = 0
            coords = line.coords

            if ctx.is_hikanji:
                if stype is not None and stype >= 0:
                    stype %= 100
                if sttType is not None and sttType >= 0:
                    sttType %= 100
                if endType is not None and endType >= 0:
                    endType %= 100

            if stype == 99:
                if lendata not in (8, 11):
                    # 列数異常（99）
                    return E.WRONG_NUMBER_OF_COLUMNS(line)
                if lendata == 11 and ctx.glyph.is_alias:
                    # エイリアスに11列
                    return E.ALIAS_11_COLUMNS(line)
            elif stype == 0:
                if lendata not in (4, 7):
                    # 列数異常（0）
                    return E.WRONG_NUMBER_OF_COLUMNS(line)
            else:
                if stype is None or stype not in datalens:
                    # 未定義の筆画
                    return E.UNKNOWN_STROKE_TYPE(line)
                l = datalens[stype]
                if lendata < l:
                    # 列不足
                    return E.TOO_FEW_COLUMNS(line)
                if lendata > l:
                    if any(n != 0 for n in line.data[l:]):
                        # 列余分（非ゼロ）
                        return E.TOO_MANY_NONZERO_COLUMNS(line)
                    # 列余分（ゼロ値）
                    return E.TOO_MANY_ZERO_COLUMNS(line)
            if stype == 0:
                if (line.data[1] == 0 and line.data[3] != 0) or \
                   (line.data[1] == -1 and line.data[3] != -1):
                    # 不正なデータ（0）
                    return E.INVALID_DATA_0(line)
            elif stype == 9:
                # 部品位置
                return E.BUHIN_ICHI(line)
            if coords is not None:
                if stype == 1:
                    if isYoko(*coords[0], *coords[1]):
                        if sttType in (12, 22, 32) or \
                                endType in (32, 13, 23, 24, 313, 413):
                            # 横画に接続(縦)型
                            return E.VERTCONN_IN_HORI_LINE(line)
                    elif sttType == 2 or endType == 2:
                        # 縦画に接続(横)型
                        return E.HORICONN_IN_VERT_LINE(line)
                elif stype == 3:
                    if isYoko(*coords[0], *coords[1]):
                        # 折れの前半が横
                        return E.HORIZONTAL_ORE_FIRST(line)
                    if line.tail_type == 5 and coords[2][0] == coords[1][0]:
                        # 折れの後半が縦
                        return E.VERTICAL_ORE_LAST(line)
                elif stype == 4:
                    if isYoko(*coords[0], *coords[1]):
                        # 乙の前半が横
                        return E.HORIZONTAL_OTSU_FIRST(line)
                    if line.tail_type == 5 and coords[2][0] <= coords[1][0]:
                        # 乙の後半が左向き
                        return E.LEFTWARD_OTSU_LAST(line)
            if stype != 99:
                strokeKeijo = (stype, sttType, endType)

                if strokeKeijo not in keijoKumiawase and not (
                        ctx.is_hikanji and
                        strokeKeijo in hikanjiKeijoKumiawase):
                    # 未定義の形状の組み合わせ
                    return E.UNKNOWN_STROKE_FORM(line)
        return False

    def record(self, glyphname, error):
        key, param = error
        super().record(glyphname, (key, (
            ":".join(param.line.strdata.split(":", 3)[:3]),
            *param
        )))

    def get_result(self):
        for val in self.results.values():
            val.sort(key=lambda r: r[1])
        return super(IllegalValidator, self).get_result()
