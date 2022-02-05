from gwv.dump import Dump, DumpEntry
import gwv.filters as filters
from gwv.helper import isKanji
from gwv.helper import isYoko
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    UNKNOWN_STROKE_TYPE="0",  # 未定義の筆画
    TOO_FEW_COLUMNS="1",  # 列不足
    TOO_MANY_NONZERO_COLUMNS="2",  # 列余分（非ゼロ）
    TOO_MANY_ZERO_COLUMNS="3",  # 列余分（ゼロ値）
    WRONG_NUMBER_OF_COLUMNS="4",  # 列数異常（99）
    INVALID_DATA_0="5",  # 不正なデータ（0）
    UNKNOWN_STROKE_FORM="6",  # 未定義の形状の組み合わせ
    ALIAS_11_COLUMNS="7",  # エイリアスに11列

    VERTCONN_IN_HORI_LINE="10",  # 横画に接続(縦)型
    HORICONN_IN_VERT_LINE="11",  # 縦画に接続(横)型
    HORIZONTAL_ORE_FIRST="30",  # 折れの前半が横
    VERTICAL_ORE_LAST="31",  # 折れの後半が縦
    HORIZONTAL_OTSU_FIRST="40",  # 乙の前半が横
    LEFTWARD_OTSU_LAST="41",  # 乙の後半が左向き
    BUHIN_ICHI="9",  # 部品位置
)


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

    name = "illegal"

    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        isKanjiGlyph = isKanji(entry.name)
        for line in entry.kage.lines:
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

            if not isKanjiGlyph:
                stype = stype % 100 if stype >= 0 else stype
                sttType = sttType % 100 if sttType >= 0 else sttType
                endType = endType % 100 if endType >= 0 else endType

            if stype == 99:
                if lendata not in (8, 11):
                    # 列数異常（99）
                    return [
                        error_codes.WRONG_NUMBER_OF_COLUMNS,
                        [line.line_number, line.strdata]]
                if lendata == 11 and entry.is_alias:
                    # エイリアスに11列
                    return [
                        error_codes.ALIAS_11_COLUMNS,
                        [line.line_number, line.strdata]]
            elif stype == 0:
                if lendata not in (4, 7):
                    # 列数異常（0）
                    return [
                        error_codes.WRONG_NUMBER_OF_COLUMNS,
                        [line.line_number, line.strdata]]
            else:
                if stype not in datalens:
                    # 未定義の筆画
                    return [
                        error_codes.UNKNOWN_STROKE_TYPE,
                        [line.line_number, line.strdata]]
                l = datalens[stype]
                if lendata < l:
                    # 列不足
                    return [
                        error_codes.TOO_FEW_COLUMNS,
                        [line.line_number, line.strdata]]
                if lendata > l:
                    if any(n != 0 for n in line.data[l:]):
                        # 列余分（非ゼロ）
                        return [
                            error_codes.TOO_MANY_NONZERO_COLUMNS,
                            [line.line_number, line.strdata]]
                    # 列余分（ゼロ値）
                    return [
                        error_codes.TOO_MANY_ZERO_COLUMNS,
                        [line.line_number, line.strdata]]
            if stype == 0:
                if (line.data[1] == 0 and line.data[3] != 0) or \
                   (line.data[1] == -1 and line.data[3] != -1):
                    # 不正なデータ（0）
                    return [
                        error_codes.INVALID_DATA_0,
                        [line.line_number, line.strdata]]
            elif stype == 1:
                if sttType in (2, 12, 22, 32) or \
                        endType in (2, 32, 13, 23, 24, 313, 413):
                    if isYoko(*coords[0], *coords[1]):
                        if sttType > 2 or endType > 2:  # not in (0, 2)
                            # 横画に接続(縦)型
                            return [
                                error_codes.VERTCONN_IN_HORI_LINE,
                                [line.line_number, line.strdata]]
                    elif sttType == 2 or endType == 2:
                        # 縦画に接続(横)型
                        return [
                            error_codes.HORICONN_IN_VERT_LINE,
                            [line.line_number, line.strdata]]
            elif stype == 9:
                # 部品位置
                return [
                    error_codes.BUHIN_ICHI, [line.line_number, line.strdata]]
            elif stype == 2:
                pass
            elif stype == 3:
                if isYoko(*coords[0], *coords[1]):
                    # 折れの前半が横
                    return [
                        error_codes.HORIZONTAL_ORE_FIRST,
                        [line.line_number, line.strdata]]
                if line.tail_type == 5 and coords[2][0] - coords[1][0] == 0:
                    # 折れの後半が縦
                    return [
                        error_codes.VERTICAL_ORE_LAST,
                        [line.line_number, line.strdata]]
            elif stype == 4:
                if isYoko(*coords[0], *coords[1]):
                    # 乙の前半が横
                    return [
                        error_codes.HORIZONTAL_OTSU_FIRST,
                        [line.line_number, line.strdata]]
                if line.tail_type == 5 and coords[2][0] - coords[1][0] <= 0:
                    # 乙の後半が左向き
                    return [
                        error_codes.LEFTWARD_OTSU_LAST,
                        [line.line_number, line.strdata]]
            if stype != 99:
                strokeKeijo = (stype, sttType, endType)

                if strokeKeijo not in keijoKumiawase and (
                        isKanjiGlyph or
                        strokeKeijo not in hikanjiKeijoKumiawase):
                    # 未定義の形状の組み合わせ
                    return [
                        error_codes.UNKNOWN_STROKE_FORM,
                        [line.line_number, line.strdata]]
        return False

    def record(self, glyphname, error):
        key = error[0]
        if key not in self.results:
            self.results[key] = []
        self.results[key].append([glyphname, ":".join(
            error[1][1].split(":", 3)[:3])] + error[1:])

    def get_result(self):
        for val in self.results.values():
            val.sort(key=lambda r: r[1])
        return super(IllegalValidator, self).get_result()
