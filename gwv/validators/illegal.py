# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.helper import isKanji
from gwv.validators import filters as default_filters
from gwv.validators import ValidatorClass

filters = {
    "alias": {True, False},
    "category": default_filters["category"] - {"user-owned"}
}


keijoKumiawase = {tuple([int(x) for x in keijoStr.split(":")]) for keijoStr in (
    "0:0:0,0:-1:-1,"
    "1:0:0,1:0:13,1:0:2,1:0:23,1:0:24,1:0:313,1:0:32,1:0:4,1:12:0,1:12:13,1:12:23,1:12:24,1:12:313,1:12:32,1:12:413,1:2:0,1:2:2,1:22:0,1:22:13,1:22:23,1:22:24,1:22:313,1:22:32,1:22:4,1:22:413,1:32:0,1:32:13,1:32:23,1:32:24,1:32:313,1:32:32,1:32:4,1:32:413,"
    "2:0:5,2:0:7,2:12:7,2:22:4,2:22:5,2:22:7,2:32:4,2:32:5,2:32:7,2:7:0,2:7:4,2:7:8,"
    "3:0:0,3:0:5,3:12:0,3:12:5,3:22:5,3:32:0,3:32:5,"
    "4:0:0,4:0:5,4:22:0,4:22:5,"
    "6:0:5,6:0:7,6:12:7,6:22:4,6:22:5,6:22:7,6:32:4,6:32:5,6:32:7,6:7:0,6:7:4,6:7:8,"
    "7:0:7,7:12:7,7:32:7,"
    "9:0:0"
    ",7:22:7,3:22:0,1:0:413"  # グリフエディタではエラーになるが……
).split(",")}

hikanjiKeijoKumiawase = {tuple([int(x) for x in keijoStr.split(":")]) for keijoStr in [
    "2:32:0",  # 曲線、接続→右払い
    "6:32:0",  # 複曲線、接続→右払い
    "2:32:8",  # 曲線、接続→止め
    "6:32:8"   # 複曲線、接続→止め
]}

# {筆画タイプ: データ列数}
datalens = {
    0: 4,
    1: 7,
    2: 9,
    3: 9,
    4: 9,
    6: 11,
    7: 11,
    9: 7
}


def isYoko(x0, y0, x1, y1):
    if y0 == y1 and x0 != x1:
        return True
    dx = x1 - x0
    dy = y1 - y0
    return -dx < dy < dx


class Validator(ValidatorClass):

    name = "illegal"

    def is_invalid(self, name, related, kage, gdata, dump):
        for line in kage.lines:
            lendata = len(line.data)
            stype = line.data[0]
            if stype != 99:
                if stype not in datalens:
                    return [0, [line.line_number, line.strdata]]  # 未定義の筆画
                l = datalens[stype]
                if lendata < l:
                    return [1, [line.line_number, line.strdata]]  # 列不足
                if lendata > l:
                    if any(n != 0 for n in line.data[l:]):
                        # 列余分（非ゼロ）
                        return [2, [line.line_number, line.strdata]]
                    return [3, [line.line_number, line.strdata]]  # 列余分（ゼロ値）
            elif lendata != 8 and lendata != 11:
                return [4, [line.line_number, line.strdata]]  # 列数異常（99）
            elif lendata == 11 and kage.isAlias():
                return [7, [line.line_number, line.strdata]]  # エイリアスに11列
            if stype == 0:
                if (line.data[1] == 0 and line.data[3] != 0) or \
                   (line.data[1] == -1 and line.data[3] != -1):
                    # 0:0:0, 0:-1:-1以外はkeijoKumiawaseで弾かれる
                    return [5, [line.line_number, line.strdata]]  # 不正なデータ（0）
            elif stype == 1:
                sttType = line.data[1]
                endType = line.data[2]
                if sttType in (2, 12, 22, 32) or endType in (2, 32, 13, 23, 24, 313, 413):
                    if isYoko(*line.data[3:7]):
                        if sttType > 2 or endType > 2:  # not in (0, 2)
                            # 横画に接続(縦)型
                            return [10, [line.line_number, line.strdata]]
                    elif sttType == 2 or endType == 2:
                        # 縦画に接続(横)型
                        return [11, [line.line_number, line.strdata]]
            elif stype == 9:
                return [9, [line.line_number, line.strdata]]  # 部品位置
            elif stype == 2:
                pass
            elif stype == 3:
                if isYoko(*line.data[3:7]):
                    return [30, [line.line_number, line.strdata]]  # 折れの前半が横
                if line.data[2] == 5 and line.data[7] - line.data[5] == 0:
                    return [31, [line.line_number, line.strdata]]  # 折れの後半が縦
            elif stype == 4:
                if isYoko(*line.data[3:7]):
                    return [40, [line.line_number, line.strdata]]  # 乙の前半が横
                if line.data[2] == 5 and line.data[7] - line.data[5] <= 0:
                    return [41, [line.line_number, line.strdata]]  # 乙の後半が左向き
            if stype != 99:
                strokeKeijo = tuple(line.data[0:3])
                if strokeKeijo not in keijoKumiawase and (isKanji(name) or strokeKeijo not in hikanjiKeijoKumiawase):
                    # 未定義の形状の組み合わせ
                    return [6, [line.line_number, line.strdata]]
        return False

    def record(self, glyphname, error):
        key = error[0]
        if key not in self.results:
            self.results[key] = []
        self.results[key].append([glyphname, ":".join(error[1][1].split(":", 3)[:3])] + error[1:])

    def get_result(self):
        for val in self.results.values():
            val.sort(key=lambda r: r[1])
        return super(Validator, self).get_result()
