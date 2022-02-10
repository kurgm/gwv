import itertools
import re
from typing import Any, List, Literal, NamedTuple, Optional

import gwv.filters as filters
from gwv.helper import isYoko
from gwv.kagedata import KageLine
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class CornerError(NamedTuple):
    vertline: list  # kage line number and data
    horiline: list  # kage line number and data


class CornerValidatorError(ValidatorErrorEnum):
    @error_code("00")
    class DISCONNECTED_TOPLEFT(CornerError):
        """左上近い"""
    @error_code("11")
    class DISCONNECTED_BOTTOMLEFT(CornerError):
        """左下近い"""
    @error_code("22")
    class DISCONNECTED_TOPRIGHT(CornerError):
        """右上近い"""
    @error_code("33")
    class DISCONNECTED_BOTTOMRIGHT(CornerError):
        """右下近い"""
    @error_code("44")
    class DISCONNECTED_BOTTOMLEFTZHOLD(CornerError):
        """左下近い"""
    @error_code("66")
    class DISCONNECTED_BOTTOMLEFTZHNEW(CornerError):
        """左下近い"""
    @error_code("77")
    class DISCONNECTED_HORICONN(CornerError):
        """接続(横)近い"""
    @error_code("99")
    class DISCONNECTED_VERTCONN(CornerError):
        """接続(縦)近い"""
    @error_code("aa")
    class DISCONNECTED_BOTTOMRIGHTHT(CornerError):
        """右下H/T近い"""

    @error_code("20")
    class TOPLEFT_ON_TOPRIGHT(CornerError):
        """右上に左上型"""
    @error_code("90")
    class TOPLEFT_ON_VERTCONN(CornerError):
        """接続(縦)に左上型"""

    @error_code("31")
    class BOTTOMLEFT_ON_BOTTOMRIGHT(CornerError):
        """右下に左下型"""
    @error_code("41")
    class BOTTOMLEFT_ON_BOTTOMLEFTZHOLD(CornerError):
        """左下zh用旧に左下型"""
    @error_code("61")
    class BOTTOMLEFT_ON_BOTTOMLEFTZHNEW(CornerError):
        """左下zh用新に左下型"""
    @error_code("91")
    class BOTTOMLEFT_ON_VERTCONN(CornerError):
        """接続(縦)に左下型"""

    @error_code("02")
    class TOPRIGHT_ON_TOPLEFT(CornerError):
        """左上に右上型"""
    @error_code("92")
    class TOPRIGHT_ON_VERTCONN(CornerError):
        """接続(縦)に右上型"""

    @error_code("13")
    class BOTTOMRIGHT_ON_BOTTOMLEFT(CornerError):
        """左下に右下型"""
    @error_code("93")
    class BOTTOMRIGHT_ON_VERTCONN(CornerError):
        """接続(縦)に右下型"""

    @error_code("14")
    class BOTTOMLEFTZHOLD_ON_BOTTOMLEFT(CornerError):
        """左下に左下zh用旧型"""
    @error_code("34")
    class BOTTOMLEFTZHOLD_ON_BOTTOMRIGHT(CornerError):
        """右下に左下zh用旧型"""
    @error_code("64")
    class BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW(CornerError):
        """左下zh用新に左下zh用旧型"""
    @error_code("94")
    class BOTTOMLEFTZHOLD_ON_VERTCONN(CornerError):
        """接続(縦)に左下zh用旧型"""

    @error_code("a5")
    class PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT(CornerError):
        """右下H/Tに擬似右下H/T型"""

    @error_code("16")
    class BOTTOMLEFTZHNEW_ON_BOTTOMLEFT(CornerError):
        """左下に左下zh用新型"""
    @error_code("36")
    class BOTTOMLEFTZHNEW_ON_BOTTOMRIGHT(CornerError):
        """右下に左下zh用新型"""
    @error_code("46")
    class BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD(CornerError):
        """左下zh用旧に左下zh用新型"""
    @error_code("96")
    class BOTTOMLEFTZHNEW_ON_VERTCONN(CornerError):
        """接続(縦)に左下zh用新型"""

    @error_code("08")
    class OPEN_ON_TOPLEFT(CornerError):
        """左上に開放型"""
    @error_code("18")
    class OPEN_ON_BOTTOMLEFT(CornerError):
        """左下に開放型"""
    @error_code("28")
    class OPEN_ON_TOPRIGHT(CornerError):
        """右上に開放型"""
    @error_code("38")
    class OPEN_ON_BOTTOMRIGHTHT(CornerError):
        """右下に開放型"""
    @error_code("48")
    class OPEN_ON_BOTTOMLEFTZHOLD(CornerError):
        """左下zh用旧に開放型"""
    @error_code("78")
    class OPEN_ON_HORICONN(CornerError):
        """接続(横)に開放型"""
    @error_code("98")
    class OPEN_ON_VERTCONN(CornerError):
        """接続(縦)に開放型"""

    @error_code("09")
    class VERTCONN_ON_TOPLEFT(CornerError):
        """左上に接続型"""
    @error_code("19")
    class VERTCONN_ON_BOTTOMLEFT(CornerError):
        """左下に接続型"""
    @error_code("29")
    class VERTCONN_ON_TOPRIGHT(CornerError):
        """右上に接続型"""
    @error_code("39")
    class VERTCONN_ON_BOTTOMRIGHTHT(CornerError):
        """右下に接続型"""

    @error_code("1a")
    class BOTTOMRIGHTHT_ON_BOTTOMLEFT(CornerError):
        """左下に右下H/T"""
    @error_code("9a")
    class BOTTOMRIGHTHT_ON_VERTCONN(CornerError):
        """接続(縦)に右下H/T"""


E = CornerValidatorError


class Stroke:

    def __init__(self, line: KageLine):
        self.line = line
        self.stype = line.stroke_type


def setSegments(stroke: Stroke, tate: List["Segment"], yoko: List["Segment"]):
    if len(stroke.line.data) <= 2:
        return
    sttType = stroke.line.head_type
    endType = stroke.line.tail_type
    coords = stroke.line.coords

    if stroke.stype == 1:
        # 直線
        seg = Segment(stroke, sttType, endType, *coords[0], *coords[1])
        if seg.isYoko():
            yoko.append(seg)
        else:
            tate.append(seg)

    elif stroke.stype in (2, 6):
        # 曲線, 複曲線
        stt = coords[0]
        end = coords[2] if stroke.stype == 2 else coords[3]
        if sttType in (12, 22, 32):
            # 左上カド, 右上カド, 接続
            seg = Segment(stroke, sttType, _STYLE_NO_END, *stt, *end, False)
            tate.append(seg)
        if endType == 7 and stt[0] > end[0]:
            # 左払い(「臼」の左上などを横画と同一視する)
            seg = Segment(stroke, 2, _STYLE_NO_END, *end, *stt, False)
            yoko.append(seg)

    elif stroke.stype in (3, 4, 7):
        # 折れ, 乙線, 縦払い
        seg = Segment(stroke, sttType, _STYLE_NO_END, *coords[0], *coords[1])
        if seg.isYoko():
            yoko.append(seg)
        else:
            tate.append(seg)

        if stroke.stype == 7 and endType == 7 and \
                coords[1][0] > coords[3][0]:
            # 左払い(「臼」の左上などを横画と同一視する)
            seg = Segment(
                stroke, 2, _STYLE_NO_END, *coords[3], *coords[1], False)
            yoko.append(seg)


class Segment:

    def __init__(self, stroke: Stroke,
                 start_type: int, end_type: int,
                 x0: int, y0: int, x1: int, y1: int,
                 is_straight_line: bool = True):

        if is_straight_line:
            if x1 < x0 if isYoko(x0, y0, x1, y1) else y1 < y0:
                start_type, end_type = end_type, start_type
                x0, x1 = x1, x0
                y0, y1 = y1, y0

        self.stroke = stroke
        self.start_type = start_type
        self.end_type = end_type
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.mid_connectable = is_straight_line
        self.sttConnect: Optional[Connection] = None
        self.midConnect: List[Connection] = []
        self.endConnect: Optional[Connection] = None

    def isVert(self):
        return self.x0 == self.x1

    def isHori(self):
        return self.y0 == self.y1

    def isYoko(self):
        return isYoko(self.x0, self.y0, self.x1, self.y1)


class Connection(NamedTuple):
    tate: Segment
    yoko: Segment
    tate_pos: Literal[0, 1, 2]
    yoko_pos: Literal[0, 1, 2]
    errcls: Any


def connect(tate: Segment, yoko: Segment,
            tate_pos: Literal[0, 1, 2], yoko_pos: Literal[0, 1, 2],
            errcls: Any):

    if tate_pos == 0:
        if tate.sttConnect is not None and tate.sttConnect.errcls is _NO_ERROR:
            return
    elif tate_pos == 2:
        if tate.endConnect is not None and tate.endConnect.errcls is _NO_ERROR:
            return

    if yoko_pos == 0:
        if yoko.sttConnect is not None and yoko.sttConnect.errcls is _NO_ERROR:
            return
    elif yoko_pos == 2:
        if yoko.endConnect is not None and yoko.endConnect.errcls is _NO_ERROR:
            return

    connection = Connection(tate, yoko, tate_pos, yoko_pos, errcls)

    def disconnect(old_connection: Connection):
        if old_connection.tate_pos == 0:
            old_connection.tate.sttConnect = None
        elif old_connection.tate_pos == 1:
            old_connection.tate.midConnect.remove(old_connection)
        elif old_connection.tate_pos == 2:
            old_connection.tate.endConnect = None

        if old_connection.yoko_pos == 0:
            old_connection.yoko.sttConnect = None
        elif old_connection.yoko_pos == 1:
            old_connection.yoko.midConnect.remove(old_connection)
        elif old_connection.yoko_pos == 2:
            old_connection.yoko.endConnect = None

    if tate_pos == 0:
        if tate.sttConnect is not None:
            disconnect(tate.sttConnect)
        tate.sttConnect = connection
    elif tate_pos == 1:
        tate.midConnect.append(connection)
    elif tate_pos == 2:
        if tate.endConnect is not None:
            disconnect(tate.endConnect)
        tate.endConnect = connection

    if yoko_pos == 0:
        if yoko.sttConnect is not None:
            disconnect(yoko.sttConnect)
        yoko.sttConnect = connection
    elif yoko_pos == 1:
        yoko.midConnect.append(connection)
    elif yoko_pos == 2:
        if yoko.endConnect is not None:
            disconnect(yoko.endConnect)
        yoko.endConnect = connection


def is_ZH_corner(t: Segment, yoko: List[Segment], _tate: List[Segment]):
    # 縦画tの終端が左下zh用カドであるべきかどうかを周辺の画の接続関係から推測する
    # 参照: https://twitter.com/kurgm/status/545573760267329537
    y = t.endConnect.yoko

    # 　┐
    # └┘
    # but not
    # ┐┐
    # └┘
    if (t.isVert() and (t.sttConnect is None or t.sttConnect.yoko_pos != 2) and
            y.endConnect is not None and y.endConnect.tate_pos == 2):
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
                    if oy.sttConnect is None and \
                       oy.end_type != _STYLE_NO_END and \
                       oy.endConnect is not None and \
                       oy.endConnect.tate_pos == 1 and \
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
        if t2Type == 3 and y2.endConnect is not None and \
                y2.endConnect.tate_pos == 0:
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
                       if my.endConnect is not None and
                       my.endConnect.tate_pos == 1):
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
                        py.end_type == 0 and \
                        py.x0 < y.x0 and py.x1 > y.x1 and \
                        ymin < py.y0 < ymax and ymin < py.y1 < ymax:
                    return False

    return True


_CORNER_ON_VERTCONN_ERRCLS = {
    12: E.TOPLEFT_ON_VERTCONN,
    13: E.BOTTOMLEFT_ON_VERTCONN,
    22: E.TOPRIGHT_ON_VERTCONN,
    23: E.BOTTOMRIGHT_ON_VERTCONN,
    313: E.BOTTOMLEFTZHOLD_ON_VERTCONN,
    413: E.BOTTOMLEFTZHNEW_ON_VERTCONN,
    24: E.BOTTOMRIGHTHT_ON_VERTCONN,
}

_re_gdesign = re.compile(r"u[0-9a-f]+-[gi](\d{2})?|zihai-\d{6}")
_re_tdesign = re.compile(r"u[0-9a-f]+-[th](\d{2})?|twedu-.+|lgccc-.+|hka-.+")

_STYLE_NO_END = -1

_NO_ERROR = object()


class CornerValidator(Validator):

    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    @filters.check_only(-filters.is_hikanji)
    @filters.check_only(-filters.has_transform)
    def is_invalid(self, ctx: ValidatorContext):
        strokes = []
        tate: List[Segment] = []
        yoko: List[Segment] = []
        isGdesign = bool(_re_gdesign.fullmatch(ctx.glyph.name))
        isTdesign = bool(_re_tdesign.fullmatch(ctx.glyph.name))

        strokes = [Stroke(line) for line in ctx.glyph.kage.lines]
        for stroke in strokes:
            setSegments(stroke, tate, yoko)

        for t in tate:
            for y in yoko:
                if t.stroke.stype in (2, 6) and y.stroke.stype in (2, 6, 7):
                    continue

                if t.start_type in (0, 12, 22, 32):
                    # 左上
                    errcls = None
                    xDif = y.x0 - t.x0
                    yDif = y.y0 - t.y0
                    if y.start_type != _STYLE_NO_END and -7 <= xDif <= 9:
                        if t.start_type == 12:
                            if 0 == xDif == yDif or \
                                    y.stroke.stype in (2, 6, 7):
                                errcls = _NO_ERROR
                            elif -5 <= yDif <= 3:
                                # 左上近い
                                errcls = E.DISCONNECTED_TOPLEFT
                        elif t.start_type == 22:
                            if -5 <= yDif <= 5:
                                # 左上に右上型
                                errcls = E.TOPRIGHT_ON_TOPLEFT
                        elif t.start_type == 0:
                            if 0 <= yDif <= 6:
                                # 左上に開放型
                                errcls = E.OPEN_ON_TOPLEFT
                        elif t.start_type == 32:
                            if -5 <= yDif <= 0:
                                # 左上に接続型
                                errcls = E.VERTCONN_ON_TOPLEFT
                    if errcls is not None:
                        connect(t, y, 0, 0, errcls)

                    # 右上
                    errcls = None
                    xDif = y.x1 - t.x0
                    yDif = y.y1 - t.y0
                    if y.end_type != _STYLE_NO_END and -7 <= xDif <= 9:
                        if t.start_type == 12:
                            if -5 <= yDif <= 3:
                                # 右上に左上型
                                errcls = E.TOPLEFT_ON_TOPRIGHT
                        elif t.start_type == 22:
                            if 0 == xDif == yDif:
                                errcls = _NO_ERROR
                            elif -5 <= yDif <= 5:
                                # 右上近い
                                errcls = E.DISCONNECTED_TOPRIGHT
                        elif t.start_type == 0:
                            if 0 <= yDif <= 6:
                                # 右上に開放型
                                errcls = E.OPEN_ON_TOPRIGHT
                        elif t.start_type == 32:
                            if -5 <= yDif <= 0:
                                # 右上に接続型
                                errcls = E.VERTCONN_ON_TOPRIGHT
                    if errcls is not None:
                        if y.end_type == 0:
                            # 接続(横)に開放型
                            errcls = E.OPEN_ON_HORICONN
                        connect(t, y, 0, 2, errcls)

                if t.end_type in (0, 13, 313, 413, 23, 24, 32):
                    # 左下
                    errcls = None
                    xDif = y.x0 - t.x1
                    yDif = y.y0 - t.y1
                    if y.start_type != _STYLE_NO_END and -8 <= xDif <= 8:
                        if t.end_type == 13:
                            if 0 == xDif == yDif:
                                errcls = _NO_ERROR
                            elif -2 <= yDif <= 4:
                                # 左下近い
                                errcls = E.DISCONNECTED_BOTTOMLEFT
                        elif t.end_type == 313:
                            if 0 == xDif == yDif:
                                if isGdesign:
                                    # 左下zh用新に左下zh用旧型
                                    errcls = E.\
                                        BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW
                                else:
                                    errcls = _NO_ERROR
                            elif -14 <= yDif <= 4:
                                errcls = E.\
                                    DISCONNECTED_BOTTOMLEFTZHOLD  # 左下zh用旧近い
                        elif t.end_type == 413:
                            if 0 == xDif == yDif:
                                if isTdesign:
                                    # 左下zh用旧に左下zh用新型
                                    errcls = E.\
                                        BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD
                                else:
                                    errcls = _NO_ERROR
                            elif -14 <= yDif <= 4:
                                errcls = E.\
                                    DISCONNECTED_BOTTOMLEFTZHNEW  # 左下zh用新近い
                        elif t.end_type == 23:
                            if -6 <= yDif <= 4:
                                errcls = E.\
                                    BOTTOMRIGHT_ON_BOTTOMLEFT  # 左下に右下型
                        elif t.end_type == 24:
                            if -6 <= yDif <= 4:
                                errcls = E.\
                                    BOTTOMRIGHTHT_ON_BOTTOMLEFT  # 左下に右下H/T型
                        elif t.end_type == 0:
                            if -19 <= yDif <= -2:
                                # 左下に開放型
                                errcls = E.OPEN_ON_BOTTOMLEFT
                            elif -1 <= yDif <= 4:
                                # 左下zh用旧に開放型
                                errcls = E.OPEN_ON_BOTTOMLEFTZHOLD
                        elif t.end_type == 32:
                            if 0 <= yDif <= 4:
                                # 左下に接続型 | 左下zh用かも？
                                errcls = E.VERTCONN_ON_BOTTOMLEFT
                    if errcls is not None:
                        connect(t, y, 2, 0, errcls)

                    # 右下
                    errcls = None
                    xDif = y.x1 - t.x1
                    yDif = y.y1 - t.y1
                    if y.end_type == 0 and t.end_type == 32 and \
                            6 <= xDif <= 18 and 0 <= yDif <= 8:
                        # 右下H/Tに擬似右下H/T型
                        errcls = E.\
                            PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT
                    elif y.end_type != _STYLE_NO_END and -8 <= xDif <= 8:
                        if t.end_type == 13:
                            if -2 <= yDif <= 4:
                                errcls = E.\
                                    BOTTOMLEFT_ON_BOTTOMRIGHT  # 右下に左下型
                        elif t.end_type == 313:
                            if -14 <= yDif <= 4:
                                errcls = E.\
                                    BOTTOMLEFTZHOLD_ON_BOTTOMRIGHT  # 右下に左下zh用旧
                        elif t.end_type == 413:
                            if -14 <= yDif <= 4:
                                errcls = E.\
                                    BOTTOMLEFTZHNEW_ON_BOTTOMRIGHT  # 右下に左下zh用新
                        elif t.end_type == 23:
                            if 0 == xDif == yDif:
                                errcls = _NO_ERROR
                            elif -6 <= yDif <= 4:
                                errcls = E.\
                                    DISCONNECTED_BOTTOMRIGHT  # 右下近い
                        elif t.end_type == 24:
                            if 0 == xDif == yDif:
                                errcls = _NO_ERROR
                            elif -6 <= yDif <= 4:
                                errcls = E.\
                                    DISCONNECTED_BOTTOMRIGHTHT  # 右下H/T近い
                        elif t.end_type == 0:
                            if -19 <= yDif <= -2:
                                # 右下に開放型
                                errcls = E.OPEN_ON_BOTTOMRIGHTHT
                        elif t.end_type == 32:
                            if -19 <= yDif <= 0:
                                errcls = E.\
                                    VERTCONN_ON_BOTTOMRIGHTHT  # 右下に接続型
                    if errcls is not None:
                        if y.end_type == 0 and 0 <= xDif and \
                                errcls != E.\
                                PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT:
                            # 接続(横)に開放型
                            errcls = E.OPEN_ON_HORICONN
                        connect(t, y, 2, 2, errcls)

            for y in yoko:
                if not (y.mid_connectable and y.isHori()):
                    continue
                # T
                tx0_min = y.x0 + 7 \
                    if y.start_type != _STYLE_NO_END and y.sttConnect is None \
                    else y.x0
                tx0_max = y.x1 - 9 \
                    if y.end_type != _STYLE_NO_END and y.endConnect is None \
                    else y.x1
                if (t.sttConnect is None or t.sttConnect.yoko != y) and \
                        t.start_type != _STYLE_NO_END and \
                        y.y0 - 5 <= t.y0 <= y.y0 + 5 and \
                        tx0_min < t.x0 < tx0_max:
                    errcls = None
                    if y.y0 == t.y0:
                        errcls = _NO_ERROR
                    elif t.start_type != 0:
                        errcls = E.DISCONNECTED_VERTCONN  # 接続(縦)近い
                    if t.start_type is not None and \
                            t.start_type in _CORNER_ON_VERTCONN_ERRCLS:
                        # 接続(縦)にカド型
                        errcls = _CORNER_ON_VERTCONN_ERRCLS[t.start_type]
                    elif t.start_type == 0 and t.y0 <= y.y0 - 2:
                        errcls = E.OPEN_ON_VERTCONN  # 接続(縦)に開放型
                    if errcls is not None:
                        connect(t, y, 0, 1, errcls)

                # ⊥
                tx1_min = y.x0 + 8 \
                    if y.start_type != _STYLE_NO_END and y.sttConnect is None \
                    else y.x0
                tx1_max = y.x1 - 8 \
                    if y.end_type != _STYLE_NO_END and y.endConnect is None \
                    else y.x1
                if (t.endConnect is None or t.endConnect.yoko != y) and \
                        t.end_type != _STYLE_NO_END and \
                        y.y0 - 5 <= t.y1 <= y.y0 + 5 and \
                        tx1_min < t.x1 < tx1_max:
                    if y.y0 == t.y1:
                        errcls = _NO_ERROR
                    else:
                        errcls = E.DISCONNECTED_VERTCONN  # 接続(縦)近い
                    if t.end_type is not None and \
                            t.end_type in _CORNER_ON_VERTCONN_ERRCLS:
                        # 接続(縦)にカド型
                        errcls = _CORNER_ON_VERTCONN_ERRCLS[t.end_type]
                    elif t.end_type == 0:
                        errcls = E.OPEN_ON_VERTCONN  # 接続(縦)に開放型
                    connect(t, y, 2, 1, errcls)

        for y in yoko:
            if y.stroke.stype in (2, 6, 7):
                continue
            for t in tate:
                if not (t.mid_connectable and t.isVert()):
                    continue
                # |-
                yy0_min = t.y0 + 6 \
                    if t.start_type != _STYLE_NO_END and t.sttConnect is None \
                    else t.y0
                yy0_max = t.y1 - 19 \
                    if t.end_type != _STYLE_NO_END and t.endConnect is None \
                    else t.y1
                if (y.sttConnect is None or y.sttConnect.tate != t) and \
                        y.start_type != _STYLE_NO_END and \
                        t.x0 - 7 <= y.x0 <= t.x0 + 7 and \
                        yy0_min < y.y0 < yy0_max:
                    if t.x0 == y.x0:
                        # 頭形状「開放」と「接続(横)」は同一視する
                        errcls = _NO_ERROR
                    else:
                        errcls = E.DISCONNECTED_HORICONN  # 接続(横)近い
                    connect(t, y, 1, 0, errcls)

                # -|
                yy1_min = t.y0 + 6 \
                    if t.start_type != _STYLE_NO_END and t.sttConnect is None \
                    else t.y0
                yy1_max = t.y1 - 19 \
                    if t.end_type != _STYLE_NO_END and t.endConnect is None \
                    else t.y1
                if (y.endConnect is None or y.endConnect.tate != t) and \
                        y.end_type != _STYLE_NO_END and \
                        t.x0 - 7 <= y.x1 <= t.x0 + 7 and \
                        yy1_min < y.y1 < yy1_max:
                    errcls = None
                    if t.x0 == y.x1:
                        errcls = _NO_ERROR
                    elif y.end_type == 2:
                        errcls = E.DISCONNECTED_HORICONN  # 接続(横)近い
                    if y.end_type == 0 and t.x0 <= y.x1:
                        errcls = E.OPEN_ON_HORICONN  # 接続(横)に開放型
                    if errcls is not None:
                        connect(t, y, 1, 2, errcls)

        results = []
        for y in yoko:
            if y.sttConnect is not None and \
                    y.sttConnect.errcls is not _NO_ERROR:
                results.append([y.sttConnect.errcls,
                                y.sttConnect.tate.stroke.line.line_number,
                                y.stroke.line.line_number])
            if y.endConnect is not None and \
                    y.endConnect.errcls is not _NO_ERROR:
                results.append([y.endConnect.errcls,
                                y.endConnect.tate.stroke.line.line_number,
                                y.stroke.line.line_number])
            for conn in y.midConnect:
                if conn.errcls is not _NO_ERROR:
                    results.append([conn.errcls,
                                    conn.tate.stroke.line.line_number,
                                    y.stroke.line.line_number])

        if isGdesign or isTdesign:
            for t in tate:
                if t.endConnect is None or t.endConnect.yoko_pos != 0 or \
                        t.end_type not in (13, 313, 413):
                    continue
                y = t.endConnect.yoko
                isZH = is_ZH_corner(t, yoko, tate)
                errcls = None
                if not isZH and t.end_type == 313:
                    # 左下に左下zh用旧型
                    errcls = E.BOTTOMLEFTZHOLD_ON_BOTTOMLEFT
                if not isZH and t.end_type == 413:
                    # 左下に左下zh用新型
                    errcls = E.BOTTOMLEFTZHNEW_ON_BOTTOMLEFT
                if isZH and t.end_type == 13:
                    errcls = E.BOTTOMLEFT_ON_BOTTOMLEFTZHNEW \
                        if isGdesign else \
                        E.BOTTOMLEFT_ON_BOTTOMLEFTZHOLD  # 左下zh用に左下型
                if errcls is not None:
                    results.append([errcls,
                                    t.stroke.line.line_number,
                                    y.stroke.line.line_number])

        if results:
            # 離れているだけの接続より形状がおかしい接続を優先してエラーとする
            # 左下zh用の新旧よりその他の形状がおかしい接続を優先してエラーとする
            result = max(
                results,
                key=lambda r: 0 if r[0].errcode[0] == r[0].errcode[1] else
                50 if r[0] in (
                    E.BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD,
                    E.BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW
                ) else 100
            )
            glines = ctx.glyph.gdata.split("$")
            return result[0](
                [result[1], glines[result[1]]],
                [result[2], glines[result[2]]],
            )

        return False
