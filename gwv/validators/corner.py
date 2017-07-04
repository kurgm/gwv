# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools
import math
import re

from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DISCONNECTED_TOPLEFT="00",  # 左上近い
    DISCONNECTED_BOTTOMLEFT="11",  # 左下近い
    DISCONNECTED_TOPRIGHT="22",  # 右上近い
    DISCONNECTED_BOTTOMRIGHT="33",  # 右下近い
    DISCONNECTED_BOTTOMLEFTZHOLD="44",  # 左下近い
    DISCONNECTED_BOTTOMLEFTZHNEW="66",  # 左下近い
    DISCONNECTED_HORICONN="77",  # 接続(横)近い
    DISCONNECTED_VERTCONN="99",  # 接続(縦)近い
    DISCONNECTED_BOTTOMRIGHTHT="aa",  # 右下H/T近い

    TOPLEFT_ON_TOPRIGHT="20",  # 右上に左上型
    TOPLEFT_ON_VERTCONN="90",  # 接続(縦)に左上型

    BOTTOMLEFT_ON_BOTTOMRIGHT="31",  # 右下に左下型
    BOTTOMLEFT_ON_BOTTOMLEFTZHOLD="41",  # 左下zh用旧に左下型
    BOTTOMLEFT_ON_BOTTOMLEFTZHNEW="61",  # 左下zh用新に左下型
    BOTTOMLEFT_ON_VERTCONN="91",  # 接続(縦)に左下型

    TOPRIGHT_ON_TOPLEFT="02",  # 左上に右上型
    TOPRIGHT_ON_VERTCONN="92",  # 接続(縦)に右上型

    BOTTOMRIGHT_ON_BOTTOMLEFT="13",  # 左下に右下型
    BOTTOMRIGHT_ON_VERTCONN="93",  # 接続(縦)に右下型

    BOTTOMLEFTZHOLD_ON_BOTTOMLEFT="14",  # 左下に左下zh用旧型
    BOTTOMLEFTZHOLD_ON_BOTTOMRIGHT="34",  # 右下に左下zh用旧型
    BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW="64",  # 左下zh用新に左下zh用旧型
    BOTTOMLEFTZHOLD_ON_VERTCONN="94",  # 接続(縦)に左下zh用旧型

    PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT="a5",  # 右下H/Tに擬似右下H/T型

    BOTTOMLEFTZHNEW_ON_BOTTOMLEFT="16",  # 左下に左下zh用新型
    BOTTOMLEFTZHNEW_ON_BOTTOMRIGHT="36",  # 右下に左下zh用新型
    BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD="46",  # 左下zh用旧に左下zh用新型
    BOTTOMLEFTZHNEW_ON_VERTCONN="96",  # 接続(縦)に左下zh用新型

    OPEN_ON_TOPLEFT="08",  # 左上に開放型
    OPEN_ON_BOTTOMLEFT="18",  # 左下に開放型
    OPEN_ON_TOPRIGHT="28",  # 右上に開放型
    OPEN_ON_BOTTOMRIGHTHT="38",  # 右下に開放型
    OPEN_ON_BOTTOMLEFTZHOLD="48",  # 左下zh用旧に開放型
    OPEN_ON_HORICONN="78",  # 接続(横)に開放型
    OPEN_ON_VERTCONN="98",  # 接続(縦)に開放型

    VERTCONN_ON_TOPLEFT="09",  # 左上に接続型
    VERTCONN_ON_BOTTOMLEFT="19",  # 左下に接続型
    VERTCONN_ON_TOPRIGHT="29",  # 右上に接続型
    VERTCONN_ON_BOTTOMRIGHTHT="39",  # 右下に接続型

    BOTTOMRIGHTHT_ON_BOTTOMLEFT="1a",  # 左下に右下H/T
    BOTTOMRIGHTHT_ON_VERTCONN="9a",  # 接続(縦)に右下H/T
)


class Stroke(object):

    def __init__(self, line):
        self.line = line
        self.stype = line.data[0]
        self.tate = None
        self.yoko = None

    def setSegments(self, tate, tate_vert, yoko, yoko_hori):
        data = self.line.data
        if len(data) <= 2:
            return
        strokeType = data[0]
        sttType = data[1]
        endType = data[2]

        if strokeType == 1:
            # 直線
            seg = Segment(self, sttType, endType,
                          data[3], data[4], data[5], data[6])
            seg.reverseIfNecessary()
            if seg.isYoko():
                if seg.isHori():
                    yoko_hori.append(seg)
                self.yoko = seg
                yoko.append(seg)
            else:
                if seg.isVert():
                    tate_vert.append(seg)
                self.tate = seg
                tate.append(seg)

        elif strokeType in (2, 6):
            # 曲線, 複曲線
            stt = data[3:5]
            end = data[7:9] if strokeType == 2 else data[9:11]
            if sttType in (12, 22, 32):
                # 左上カド, 右上カド, 接続
                seg = Segment(self, sttType, _STYLE_NO_END,
                              stt[0], stt[1], end[0], end[1])
                self.tate = seg
                tate.append(seg)
            if endType == 7 and stt[0] > end[0]:
                # 左払い(「臼」の左上などを横画と同一視する)
                seg = Segment(self, 2, _STYLE_NO_END,
                              end[0], end[1], stt[0], stt[1])
                self.yoko = seg
                yoko.append(seg)

        elif strokeType in (3, 4, 7):
            # 折れ, 乙線, 縦払い
            seg = Segment(self, sttType, _STYLE_NO_END,
                          data[3], data[4], data[5], data[6])
            seg.reverseIfNecessary()
            if seg.isYoko():
                if seg.isHori():
                    yoko_hori.append(seg)
                self.yoko = seg
                yoko.append(seg)
            else:
                if seg.isVert():
                    tate_vert.append(seg)
                self.tate = seg
                tate.append(seg)

            if strokeType == 7 and endType == 7 and data[5] > data[9]:
                # 左払い(「臼」の左上などを横画と同一視する)
                seg = Segment(self, 2, _STYLE_NO_END,
                              data[9], data[10], data[5], data[6])
                self.yoko = seg
                yoko.append(seg)


class Segment(object):

    def __init__(self, stroke, start_type, end_type, x0, y0, x1, y1):
        self.stroke = stroke
        self.start_type = start_type
        self.end_type = end_type
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.sttConnect = None
        self.midConnect = []
        self.endConnect = None

    def reverse(self):
        self.start_type, self.end_type = self.end_type, self.start_type
        self.x0, self.x1 = self.x1, self.x0
        self.y0, self.y1 = self.y1, self.y0
        self.sttConnect, self.endConnect = self.endConnect, self.sttConnect

    def reverseIfNecessary(self):
        if self.isYoko():
            if self.x1 < self.x0:
                self.reverse()
        else:
            if self.y1 < self.y0:
                self.reverse()

    def isVert(self):
        return self.x0 == self.x1

    def isHori(self):
        return self.y0 == self.y1

    def getTheta(self):
        if self.x0 == self.x1 and self.y0 == self.y1:
            return math.pi / 2
        return math.atan2(self.y1 - self.y0, self.x1 - self.x0)

    def isYoko(self):
        return (self.y0 == self.y1 and self.x0 != self.x1) or -_d45 < self.getTheta() < _d45


class Connection(object):

    def __init__(self, tate, yoko, tate_pos, yoko_pos, errorNum):
        self.tate = tate
        self.yoko = yoko
        self.tate_pos = tate_pos
        self.yoko_pos = yoko_pos
        self.errorNum = errorNum

        if tate_pos == 0:
            if tate.sttConnect is not None:
                if tate.sttConnect.errorNum == _NO_ERROR:
                    return
                tate.sttConnect.disconnect()
            tate.sttConnect = self
        elif tate_pos == 1:
            tate.midConnect.append(self)
        elif tate_pos == 2:
            if tate.endConnect is not None:
                if tate.endConnect.errorNum == _NO_ERROR:
                    return
                tate.endConnect.disconnect()
            tate.endConnect = self

        if yoko_pos == 0:
            if yoko.sttConnect is not None:
                if yoko.sttConnect.errorNum == _NO_ERROR:
                    return
                yoko.sttConnect.disconnect()
            yoko.sttConnect = self
        elif yoko_pos == 1:
            yoko.midConnect.append(self)
        elif yoko_pos == 2:
            if yoko.endConnect is not None:
                if yoko.endConnect.errorNum == _NO_ERROR:
                    return
                yoko.endConnect.disconnect()
            yoko.endConnect = self

    def disconnect(self):
        if self.tate_pos == 0:
            self.tate.sttConnect = None
        elif self.tate_pos == 1:
            self.tate.midConnect.remove(self)
        elif self.tate_pos == 2:
            self.tate.endConnect = None

        if self.yoko_pos == 0:
            self.yoko.sttConnect = None
        elif self.yoko_pos == 1:
            self.yoko.midConnect.remove(self)
        elif self.yoko_pos == 2:
            self.yoko.endConnect = None


def is_ZH_corner(t, yoko, tate):
    # 縦画tの終端が左下zh用カドであるべきかどうかを周辺の画の接続関係から推測する
    # 参照: https://twitter.com/kurgm/status/545573760267329537
    y = t.endConnect.yoko

    # 　┐
    # └┘
    # but not
    # ┐┐
    # └┘
    if t.isVert() and (t.sttConnect is None or t.sttConnect.yoko_pos != 2) and \
            y.endConnect is not None and y.endConnect.tate_pos == 2:
        t2 = y.endConnect.tate
        if t2.sttConnect is not None and t2.sttConnect.yoko_pos == 2:
            return False

    # ┌┐
    # ├一
    # └
    # or
    # ┌┐
    # ├┤
    # └
    # or
    # ┌
    # ├一 ┤
    # └
    if t.sttConnect is not None and t.sttConnect.yoko_pos == 0:
        midys = [conn.yoko for conn in t.midConnect if conn.yoko_pos == 0]
        y2 = t.sttConnect.yoko
        if midys and y2.endConnect is not None and y2.endConnect.tate_pos == 0:
            if any(my.endConnect is None and my.end_type == 0 for my in midys):
                return False  # 曰・烏・鳥
            if any(my.endConnect.tate == y2.endConnect.tate for my in midys if
                   my.endConnect is not None and my.endConnect.tate_pos == 1):
                return False  # 日・目
        else:
            for my in midys:
                if my.endConnect is not None or my.end_type != 0:
                    continue
                for oy in yoko:
                    if oy == my:
                        continue
                    if oy.sttConnect is None and oy.end_type != _STYLE_NO_END and \
                       oy.endConnect is not None and oy.endConnect.tate_pos == 1 and \
                       oy.x0 > my.x1 and -4 <= oy.y0 - my.y1 <= 4:
                        return False  # 臼

    # ├┼一
    # └┴
    midys = [conn.yoko for conn in t.midConnect if conn.yoko_pos == 0 and
             conn.yoko.endConnect is None and conn.yoko.end_type == 0]
    midts = [conn.tate for conn in y.midConnect if conn.tate_pos == 2]
    for my, mt in itertools.product(midys, midts):
        if my.x1 > mt.x1 and my.y0 > mt.y0:
            return False
    # ┌─┐
    # └┐┘
    # 　╰
    if t.sttConnect is not None and t.sttConnect.yoko_pos == 0 and \
       y.endConnect is not None and y.endConnect.tate_pos == 0:
        t2Type = y.endConnect.tate.stroke.stype
        y2 = t.sttConnect.yoko
        if t2Type == 3 and y2.endConnect is not None and y2.endConnect.tate_pos == 0:
            t3 = y2.endConnect.tate
            if t3.endConnect is not None and t3.endConnect.yoko_pos == 2:
                return False
    # ┌┬
    # └┤
    # or
    # ┌┤
    # ├┤
    # └┤
    if t.sttConnect is not None and t.sttConnect.yoko_pos == 0 and \
       y.endConnect is not None and y.endConnect.tate_pos == 1:
        t2 = y.endConnect.tate
        if t2.sttConnect is not None and t2.sttConnect.yoko_pos == 1 and \
                t.sttConnect.yoko == t2.sttConnect.yoko:
            return False
        if t.midConnect:
            midys = [conn.yoko for conn in t.midConnect if conn.yoko_pos == 0]
            y2 = t.sttConnect.yoko
            if midys and \
               y2.endConnect is not None and y2.endConnect.tate_pos == 1 and \
               y2.endConnect.tate == y.endConnect.tate:
                if any(my.endConnect.tate == y2.endConnect.tate for my in midys
                       if my.endConnect is not None and my.endConnect.tate_pos == 1):
                    return False

    # 廿
    if t.sttConnect is None and t.start_type == 0 and \
            y.endConnect is not None and y.endConnect.tate_pos == 2:
        t2 = y.endConnect.tate
        if t2.sttConnect is None and t2.start_type == 0:
            ymin = max(t.y0, t2.y0)
            ymax = min(t.y1, t2.y1)
            for py in yoko:
                if py.sttConnect is py.endConnect is None and \
                        py.end_type == 0 and py.x0 < y.x0 and py.x1 > y.x1 and \
                        ymin < py.y0 < ymax and ymin < py.y1 < ymax:
                    return False

    return True


TATE_CORNER_STYLES = (12, 13, 22, 23, 313, None, 413, None, None, None, 24)

_re_gdesign = re.compile(r"^(u[0-9a-f]+-[gi](\d{2})?|zihai-\d{6})$")
_re_tdesign = re.compile(
    r"^(u[0-9a-f]+-[th](\d{2})?|twedu-.+|lgccc-.+|hka-.+)$")

_d45 = math.pi / 4

_STYLE_NO_END = -1

_NO_ERROR = -2

filters = {
    "alias": {False},
    "category": default_filters["category"] - {"user-owned", "ucs-hikanji", "ucs-hikanji-var", "koseki-hikanji"}
}


class CornerValidator(Validator):

    name = "corner"

    def is_invalid(self, name, related, kage, gdata, dump):
        strokes = []
        tate = []
        yoko = []
        tate_vert = []
        yoko_hori = []
        isGdesign = _re_gdesign.match(name)
        isTdesign = _re_tdesign.match(name)

        strokes = [Stroke(line) for line in kage.lines]
        for stroke in strokes:
            stroke.setSegments(tate, tate_vert, yoko, yoko_hori)

        for t in tate:
            for y in yoko:
                if t.stroke.stype in (2, 6) and y.stroke.stype in (2, 6, 7):
                    continue

                if t.start_type in (0, 12, 22, 32):
                    # 左上
                    errorNum = None
                    xDif = y.x0 - t.x0
                    yDif = y.y0 - t.y0
                    if y.start_type != _STYLE_NO_END and -7 <= xDif <= 9:
                        if t.start_type == 12:
                            if 0 == xDif == yDif or y.stroke.stype in (2, 6, 7):
                                errorNum = _NO_ERROR
                            elif -5 <= yDif <= 3:
                                errorNum = error_codes.DISCONNECTED_TOPLEFT  # 左上近い
                        elif t.start_type == 22:
                            if -5 <= yDif <= 5:
                                errorNum = error_codes.TOPRIGHT_ON_TOPLEFT  # 左上に右上型
                        elif t.start_type == 0:
                            if 0 <= yDif <= 6:
                                errorNum = error_codes.OPEN_ON_TOPLEFT  # 左上に開放型
                        elif t.start_type == 32:
                            if -5 <= yDif <= 0:
                                errorNum = error_codes.VERTCONN_ON_TOPLEFT  # 左上に接続型
                    if errorNum is not None:
                        Connection(t, y, 0, 0, errorNum)

                    # 右上
                    errorNum = None
                    xDif = y.x1 - t.x0
                    yDif = y.y1 - t.y0
                    if y.end_type != _STYLE_NO_END and -7 <= xDif <= 9:
                        if t.start_type == 12:
                            if -5 <= yDif <= 3:
                                errorNum = error_codes.TOPLEFT_ON_TOPRIGHT  # 右上に左上型
                        elif t.start_type == 22:
                            if 0 == xDif == yDif:
                                errorNum = _NO_ERROR
                            elif -5 <= yDif <= 5:
                                errorNum = error_codes.DISCONNECTED_TOPRIGHT  # 右上近い
                        elif t.start_type == 0:
                            if 0 <= yDif <= 6:
                                errorNum = error_codes.OPEN_ON_TOPRIGHT  # 右上に開放型
                        elif t.start_type == 32:
                            if -5 <= yDif <= 0:
                                errorNum = error_codes.VERTCONN_ON_TOPRIGHT  # 右上に接続型
                    if errorNum is not None:
                        if y.end_type == 0:
                            # 接続(横)に開放型
                            errorNum = error_codes.OPEN_ON_HORICONN
                        Connection(t, y, 0, 2, errorNum)

                if t.end_type in (0, 13, 313, 413, 23, 24, 32):
                    # 左下
                    errorNum = None
                    xDif = y.x0 - t.x1
                    yDif = y.y0 - t.y1
                    if y.start_type != _STYLE_NO_END and -8 <= xDif <= 8:
                        if t.end_type == 13:
                            if 0 == xDif == yDif:
                                errorNum = _NO_ERROR
                            elif -2 <= yDif <= 4:
                                errorNum = error_codes.DISCONNECTED_BOTTOMLEFT  # 左下近い
                        elif t.end_type == 313:
                            if 0 == xDif == yDif:
                                if isGdesign:
                                    errorNum = error_codes.BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW  # 左下zh用新に左下zh用旧型
                                else:
                                    errorNum = _NO_ERROR
                            elif -14 <= yDif <= 4:
                                errorNum = error_codes.DISCONNECTED_BOTTOMLEFTZHOLD  # 左下zh用旧近い
                        elif t.end_type == 413:
                            if 0 == xDif == yDif:
                                if isTdesign:
                                    errorNum = error_codes.BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD  # 左下zh用旧に左下zh用新型
                                else:
                                    errorNum = _NO_ERROR
                            elif -14 <= yDif <= 4:
                                errorNum = error_codes.DISCONNECTED_BOTTOMLEFTZHNEW  # 左下zh用新近い
                        elif t.end_type == 23:
                            if -6 <= yDif <= 4:
                                errorNum = error_codes.BOTTOMRIGHT_ON_BOTTOMLEFT  # 左下に右下型
                        elif t.end_type == 24:
                            if -6 <= yDif <= 4:
                                errorNum = error_codes.BOTTOMRIGHTHT_ON_BOTTOMLEFT  # 左下に右下H/T型
                        elif t.end_type == 0:
                            if -19 <= yDif <= -2:
                                errorNum = error_codes.OPEN_ON_BOTTOMLEFT  # 左下に開放型
                            elif -1 <= yDif <= 4:
                                errorNum = error_codes.OPEN_ON_BOTTOMLEFTZHOLD  # 左下zh用旧に開放型
                        elif t.end_type == 32:
                            if 0 <= yDif <= 4:
                                errorNum = error_codes.VERTCONN_ON_BOTTOMLEFT  # 左下に接続型 | 左下zh用かも？
                    if errorNum is not None:
                        Connection(t, y, 2, 0, errorNum)

                    # 右下
                    errorNum = None
                    xDif = y.x1 - t.x1
                    yDif = y.y1 - t.y1
                    if y.end_type == 0 and t.end_type == 32 and 6 <= xDif <= 18 and 0 <= yDif <= 8:
                        errorNum = error_codes.PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT  # 右下H/Tに擬似右下H/T型
                    elif y.end_type != _STYLE_NO_END and -8 <= xDif <= 8:
                        if t.end_type == 13:
                            if -2 <= yDif <= 4:
                                errorNum = error_codes.BOTTOMLEFT_ON_BOTTOMRIGHT  # 右下に左下型
                        elif t.end_type == 313:
                            if -14 <= yDif <= 4:
                                errorNum = error_codes.BOTTOMLEFTZHOLD_ON_BOTTOMRIGHT  # 右下に左下zh用旧
                        elif t.end_type == 413:
                            if -14 <= yDif <= 4:
                                errorNum = error_codes.BOTTOMLEFTZHNEW_ON_BOTTOMRIGHT  # 右下に左下zh用新
                        elif t.end_type == 23:
                            if 0 == xDif == yDif:
                                errorNum = _NO_ERROR
                            elif -6 <= yDif <= 4:
                                errorNum = error_codes.DISCONNECTED_BOTTOMRIGHT  # 右下近い
                        elif t.end_type == 24:
                            if 0 == xDif == yDif:
                                errorNum = _NO_ERROR
                            elif -6 <= yDif <= 4:
                                errorNum = error_codes.DISCONNECTED_BOTTOMRIGHTHT  # 右下H/T近い
                        elif t.end_type == 0:
                            if -19 <= yDif <= -2:
                                errorNum = error_codes.OPEN_ON_BOTTOMRIGHTHT  # 右下に開放型
                        elif t.end_type == 32:
                            if -19 <= yDif <= 0:
                                errorNum = error_codes.VERTCONN_ON_BOTTOMRIGHTHT  # 右下に接続型
                    if errorNum is not None:
                        if y.end_type == 0 and 0 <= xDif and errorNum != error_codes.PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT:
                            # 接続(横)に開放型
                            errorNum = error_codes.OPEN_ON_HORICONN
                        Connection(t, y, 2, 2, errorNum)

            for y in yoko_hori:
                # T
                tx0_min = y.x0 + 7 if y.start_type != _STYLE_NO_END and y.sttConnect is None else y.x0
                tx0_max = y.x1 - 9 if y.end_type != _STYLE_NO_END and y.endConnect is None else y.x1
                if (t.sttConnect is None or t.sttConnect.yoko != y) and \
                        t.start_type != _STYLE_NO_END and \
                        y.y0 - 5 <= t.y0 <= y.y0 + 5 and tx0_min < t.x0 < tx0_max:
                    errorNum = None
                    if y.y0 == t.y0:
                        errorNum = _NO_ERROR
                    elif t.start_type != 0:
                        errorNum = error_codes.DISCONNECTED_VERTCONN  # 接続(縦)近い
                    if t.start_type is not None and t.start_type in TATE_CORNER_STYLES:
                        errorNum = "9{:x}".format(
                            TATE_CORNER_STYLES.index(t.start_type))  # 接続(縦)にカド型
                    elif t.start_type == 0 and t.y0 <= y.y0 - 2:
                        errorNum = error_codes.OPEN_ON_VERTCONN  # 接続(縦)に開放型
                    if errorNum is not None:
                        Connection(t, y, 0, 1, errorNum)

                # ⊥
                tx1_min = y.x0 + 8 if y.start_type != _STYLE_NO_END and y.sttConnect is None else y.x0
                tx1_max = y.x1 - 8 if y.end_type != _STYLE_NO_END and y.endConnect is None else y.x1
                if (t.endConnect is None or t.endConnect.yoko != y) and \
                        t.end_type != _STYLE_NO_END and \
                        y.y0 - 5 <= t.y1 <= y.y0 + 5 and tx1_min < t.x1 < tx1_max:
                    if y.y0 == t.y1:
                        errorNum = _NO_ERROR
                    else:
                        errorNum = error_codes.DISCONNECTED_VERTCONN  # 接続(縦)近い
                    if t.end_type is not None and t.end_type in TATE_CORNER_STYLES:
                        errorNum = "9{:x}".format(
                            TATE_CORNER_STYLES.index(t.end_type))  # 接続(縦)にカド型
                    elif t.end_type == 0:
                        errorNum = error_codes.OPEN_ON_VERTCONN  # 接続(縦)に開放型
                    Connection(t, y, 2, 1, errorNum)

        for y in yoko:
            if y.stroke.stype in (2, 6, 7):
                continue
            for t in tate_vert:
                # |-
                yy0_min = t.y0 + 6 if t.start_type != _STYLE_NO_END and t.sttConnect is None else t.y0
                yy0_max = t.y1 - 19 if t.end_type != _STYLE_NO_END and t.endConnect is None else t.y1
                if (y.sttConnect is None or y.sttConnect.tate != t) and \
                        y.start_type != _STYLE_NO_END and \
                        t.x0 - 7 <= y.x0 <= t.x0 + 7 and yy0_min < y.y0 < yy0_max:
                    if t.x0 == y.x0:
                        # 頭形状「開放」と「接続(横)」は同一視する
                        errorNum = _NO_ERROR
                    else:
                        errorNum = error_codes.DISCONNECTED_HORICONN  # 接続(横)近い
                    Connection(t, y, 1, 0, errorNum)

                # -|
                yy1_min = t.y0 + 6 if t.start_type != _STYLE_NO_END and t.sttConnect is None else t.y0
                yy1_max = t.y1 - 19 if t.end_type != _STYLE_NO_END and t.endConnect is None else t.y1
                if (y.endConnect is None or y.endConnect.tate != t) and \
                        y.end_type != _STYLE_NO_END and \
                        t.x0 - 7 <= y.x1 <= t.x0 + 7 and yy1_min < y.y1 < yy1_max:
                    errorNum = None
                    if t.x0 == y.x1:
                        errorNum = _NO_ERROR
                    elif y.end_type == 2:
                        errorNum = error_codes.DISCONNECTED_HORICONN  # 接続(横)近い
                    if y.end_type == 0 and t.x0 <= y.x1:
                        errorNum = error_codes.OPEN_ON_HORICONN  # 接続(横)に開放型
                    if errorNum is not None:
                        Connection(t, y, 1, 2, errorNum)

        results = []
        for y in yoko:
            if y.sttConnect is not None and y.sttConnect.errorNum != _NO_ERROR:
                results.append([y.sttConnect.errorNum,
                                y.sttConnect.tate.stroke.line.line_number,
                                y.stroke.line.line_number])
            if y.endConnect is not None and y.endConnect.errorNum != _NO_ERROR:
                results.append([y.endConnect.errorNum,
                                y.endConnect.tate.stroke.line.line_number,
                                y.stroke.line.line_number])
            for conn in y.midConnect:
                if conn.errorNum != _NO_ERROR:
                    results.append([conn.errorNum,
                                    conn.tate.stroke.line.line_number,
                                    y.stroke.line.line_number])

        if isGdesign or isTdesign:
            for t in tate:
                if t.endConnect is None or t.endConnect.yoko_pos != 0 or \
                        t.end_type not in (13, 313, 413):
                    continue
                y = t.endConnect.yoko
                isZH = is_ZH_corner(t, tate, yoko)
                errorNum = None
                if not isZH and t.end_type == 313:
                    errorNum = error_codes.BOTTOMLEFTZHOLD_ON_BOTTOMLEFT  # 左下に左下zh用旧型
                if not isZH and t.end_type == 413:
                    errorNum = error_codes.BOTTOMLEFTZHNEW_ON_BOTTOMLEFT  # 左下に左下zh用新型
                if isZH and t.end_type == 13:
                    errorNum = error_codes.BOTTOMLEFT_ON_BOTTOMLEFTZHNEW if isGdesign else error_codes.BOTTOMLEFT_ON_BOTTOMLEFTZHOLD  # 左下zh用に左下型
                if errorNum is not None:
                    results.append([errorNum,
                                    t.stroke.line.line_number,
                                    y.stroke.line.line_number])

        if results:
            # 離れているだけの接続より形状がおかしい接続を優先してエラーとする
            # 左下zh用の新旧よりその他の形状がおかしい接続を優先してエラーとする
            result = max(
                results,
                key=lambda r: (100 if r[0] not in (
                    error_codes.BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD,
                    error_codes.BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW
                ) else 50) if r[0][0] != r[0][1] else 0)
            glines = gdata.split("$")
            return [result[0], [result[1], glines[result[1]]], [result[2], glines[result[2]]]]

        return False


validator_class = CornerValidator
