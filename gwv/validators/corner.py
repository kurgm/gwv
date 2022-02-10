import itertools
import re
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Tuple

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
        """左下zh用旧近い"""
    @error_code("66")
    class DISCONNECTED_BOTTOMLEFTZHNEW(CornerError):
        """左下zh用新近い"""
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
    class OPEN_ON_BOTTOMRIGHT(CornerError):
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
        """左下に接続型 | 左下zh用旧かも？"""
    @error_code("29")
    class VERTCONN_ON_TOPRIGHT(CornerError):
        """右上に接続型"""
    @error_code("39")
    class VERTCONN_ON_BOTTOMRIGHT(CornerError):
        """右下に接続型"""

    @error_code("1a")
    class BOTTOMRIGHTHT_ON_BOTTOMLEFT(CornerError):
        """左下に右下H/T型"""
    @error_code("9a")
    class BOTTOMRIGHTHT_ON_VERTCONN(CornerError):
        """接続(縦)に右下H/T型"""


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


def _try_connect_corner(
        tate: Segment, yoko: Segment,
        tate_pos: Literal[0, 2], yoko_pos: Literal[0, 2],
        type_map: Dict[int, List[
            Tuple[Any, Tuple[int, int], Tuple[int, int]]]],
        yoko_open_error_limit: Optional[int] = None):

    tate_type = tate.start_type if tate_pos == 0 else tate.end_type
    if tate_type not in type_map:
        return False
    yoko_type = yoko.start_type if yoko_pos == 0 else yoko.end_type
    if yoko_type == _STYLE_NO_END:
        return False

    x_dif = (yoko.x0 if yoko_pos == 0 else yoko.x1) - \
        (tate.x0 if tate_pos == 0 else tate.x1)
    y_dif = (yoko.y0 if yoko_pos == 0 else yoko.y1) - \
        (tate.y0 if tate_pos == 0 else tate.y1)

    for errcls, (x_min, x_max), (y_min, y_max) in type_map[tate_type]:
        if x_min <= x_dif <= x_max and y_min <= y_dif <= y_max:
            break
    else:
        return False

    if yoko_pos == 2 and yoko_type == 0 and (
            yoko_open_error_limit is None or yoko_open_error_limit <= x_dif):
        errcls = E.OPEN_ON_HORICONN

    connect(tate, yoko, tate_pos, yoko_pos, errcls)
    return True


def _try_connect_yoko_middle(
        tate: Segment, yoko: Segment, tate_pos: Literal[0, 2],
        yoko_limit_offsets: Tuple[int, int]):
    if not (yoko.mid_connectable and yoko.isHori()):
        return False
    yoko_y = yoko.y0

    tate_type = tate.start_type if tate_pos == 0 else tate.end_type
    if tate_type == _STYLE_NO_END:
        return False
    tate_conn = tate.sttConnect if tate_pos == 0 else tate.endConnect
    if tate_conn is not None and tate_conn.yoko == yoko:
        return False

    tate_x = tate.x0 if tate_pos == 0 else tate.x1
    tate_y = tate.y0 if tate_pos == 0 else tate.y1

    y_dif = yoko_y - tate_y
    if not (-5 <= y_dif <= 5):
        return False

    yoko_limit_off0, yoko_limit_off1 = yoko_limit_offsets
    if yoko.start_type == _STYLE_NO_END or yoko.sttConnect is not None:
        yoko_limit_off0 = 0
    if yoko.end_type == _STYLE_NO_END or yoko.endConnect is not None:
        yoko_limit_off1 = 0

    if not (yoko.x0 + yoko_limit_off0 < tate_x < yoko.x1 - yoko_limit_off1):
        return False

    if tate_type in _CORNER_ON_VERTCONN_ERRCLS:
        errcls = _CORNER_ON_VERTCONN_ERRCLS[tate_type]
    elif tate_type == 0 and (tate_pos == 2 or y_dif >= 2):
        errcls = E.OPEN_ON_VERTCONN
    elif y_dif == 0:
        errcls = _NO_ERROR
    elif tate_type != 0:
        errcls = E.DISCONNECTED_VERTCONN
    else:
        return False

    connect(tate, yoko, tate_pos, 1, errcls)
    return True


def _try_connect_tate_middle(
        tate: Segment, yoko: Segment, yoko_pos: Literal[0, 2]):
    if not (tate.mid_connectable and tate.isVert()):
        return False
    tate_x = tate.x0

    yoko_type = yoko.start_type if yoko_pos == 0 else yoko.end_type
    if yoko_type == _STYLE_NO_END:
        return False
    yoko_conn = yoko.sttConnect if yoko_pos == 0 else yoko.endConnect
    if yoko_conn is not None and yoko_conn.tate == tate:
        return False

    yoko_x = yoko.x0 if yoko_pos == 0 else yoko.x1
    yoko_y = yoko.y0 if yoko_pos == 0 else yoko.y1

    x_dif = yoko_x - tate_x
    if not (-7 <= x_dif <= 7):
        return False

    tate_limit_off0 = 6
    tate_limit_off1 = 19
    if tate.start_type == _STYLE_NO_END or tate.sttConnect is not None:
        tate_limit_off0 = 0
    if tate.end_type == _STYLE_NO_END or tate.endConnect is not None:
        tate_limit_off1 = 0

    if not (tate.y0 + tate_limit_off0 < yoko_y < tate.y1 - tate_limit_off1):
        return False

    if yoko_pos == 2 and yoko_type == 0 and x_dif >= 0:
        errcls = E.OPEN_ON_HORICONN
    elif x_dif == 0:
        # 頭形状「開放」と「接続(横)」は同一視する
        errcls = _NO_ERROR
    elif yoko_pos == 0 or yoko_type == 2:
        errcls = E.DISCONNECTED_HORICONN
    else:
        return False

    connect(tate, yoko, 1, yoko_pos, errcls)
    return True


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

                # 左上
                if y.stroke.stype in (2, 6, 7) and \
                        y.start_type != _STYLE_NO_END and \
                        t.start_type == 12 and \
                        -7 <= y.x0 - t.x0 <= 9:
                    # bug: missing constraint on yDif
                    connect(t, y, 0, 0, _NO_ERROR)
                else:
                    _try_connect_corner(t, y, 0, 0, {
                        12: [
                            (_NO_ERROR, (0, 0), (0, 0)),
                            (E.DISCONNECTED_TOPLEFT, (-7, 9), (-5, 3)),
                        ],
                        22: [(E.TOPRIGHT_ON_TOPLEFT, (-7, 9), (-5, 5))],
                        0: [(E.OPEN_ON_TOPLEFT, (-7, 9), (0, 6))],
                        32: [(E.VERTCONN_ON_TOPLEFT, (-7, 9), (-5, 0))],
                    })

                # 右上
                _try_connect_corner(t, y, 0, 2, {
                    12: [(E.TOPLEFT_ON_TOPRIGHT, (-7, 9), (-5, 3))],
                    22: [
                        (_NO_ERROR, (0, 0), (0, 0)),
                        (E.DISCONNECTED_TOPRIGHT, (-7, 9), (-5, 5)),
                    ],
                    0: [(E.OPEN_ON_TOPRIGHT, (-7, 9), (0, 6))],
                    32: [(E.VERTCONN_ON_TOPRIGHT, (-7, 9), (-5, 0))],
                })

                # 左下
                _try_connect_corner(t, y, 2, 0, {
                    13: [
                        (_NO_ERROR, (0, 0), (0, 0)),
                        (E.DISCONNECTED_BOTTOMLEFT, (-8, 8), (-2, 4)),
                    ],
                    313: [
                        (E.BOTTOMLEFTZHOLD_ON_BOTTOMLEFTZHNEW if isGdesign else
                         _NO_ERROR,
                         (0, 0), (0, 0)),
                        (E.DISCONNECTED_BOTTOMLEFTZHOLD, (-8, 8), (-14, 4)),
                    ],
                    413: [
                        (E.BOTTOMLEFTZHNEW_ON_BOTTOMLEFTZHOLD if isTdesign else
                         _NO_ERROR,
                         (0, 0), (0, 0)),
                        (E.DISCONNECTED_BOTTOMLEFTZHNEW, (-8, 8), (-14, 4)),
                    ],
                    23: [(E.BOTTOMRIGHT_ON_BOTTOMLEFT, (-8, 8), (-6, 4))],
                    24: [(E.BOTTOMRIGHTHT_ON_BOTTOMLEFT, (-8, 8), (-6, 4))],
                    0: [
                        (E.OPEN_ON_BOTTOMLEFT, (-8, 8), (-19, -2)),
                        (E.OPEN_ON_BOTTOMLEFTZHOLD, (-8, 8), (-1, 4))
                    ],
                    32: [(E.VERTCONN_ON_BOTTOMLEFT, (-8, 8), (0, 4))],
                })

                # 右下
                if y.end_type == 0 and t.end_type == 32 and \
                        6 <= y.x1 - t.x1 <= 18 and 0 <= y.y1 - t.y1 <= 8:
                    connect(t, y, 2, 2, E.PSEUDOBOTTOMRIGHTHT_ON_BOTTOMRIGHTHT)
                else:
                    _try_connect_corner(t, y, 2, 2, {
                        13: [(E.BOTTOMLEFT_ON_BOTTOMRIGHT, (-8, 8), (-2, 4))],
                        313: [(E.BOTTOMLEFTZHOLD_ON_BOTTOMRIGHT,
                               (-8, 8), (-14, 4))],
                        413: [(E.BOTTOMLEFTZHNEW_ON_BOTTOMRIGHT,
                               (-8, 8), (-14, 4))],
                        23: [
                            (_NO_ERROR, (0, 0), (0, 0)),
                            (E.DISCONNECTED_BOTTOMRIGHT, (-8, 8), (-6, 4)),
                        ],
                        24: [
                            (_NO_ERROR, (0, 0), (0, 0)),
                            (E.DISCONNECTED_BOTTOMRIGHTHT, (-8, 8), (-6, 4)),
                        ],
                        0: [(E.OPEN_ON_BOTTOMRIGHT, (-8, 8), (-19, -2))],
                        32: [(E.VERTCONN_ON_BOTTOMRIGHT, (-8, 8), (-19, 0))],
                    }, 0)

            for y in yoko:
                # T
                _try_connect_yoko_middle(t, y, 0, (7, 9))
                # ⊥
                _try_connect_yoko_middle(t, y, 2, (8, 8))

        for y in yoko:
            if y.stroke.stype in (2, 6, 7):
                continue
            for t in tate:
                # |-
                _try_connect_tate_middle(t, y, 0)
                # -|
                _try_connect_tate_middle(t, y, 2)

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
