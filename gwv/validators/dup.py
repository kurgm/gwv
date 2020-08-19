import math
from typing import List, Tuple

from gwv.dump import Dump
from gwv.helper import isKanji
from gwv.kagedata import KageData, KageLine
from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    HORILINE="10",  # 横
    VERTLINE="11",  # 縦
    CURVE="2",  # 曲線
    CCURVE="3",  # 複曲線
    PART="99",  # 部品
    PARTPOS="9",  # 部品位置
)


_d45 = math.pi / 4.0


class LineSegment:

    def __init__(self, line: KageLine, dist: float, angle: float,
                 t0: int, t1: int):
        self.line = line
        self.dist = dist  # (0, 0)と直線との距離
        self.angle = angle  # yoko: -pi/4 < theta < pi/4; tate: 0 < theta < pi
        self.t0 = t0
        self.t1 = t1


def addLine(line: KageLine, tate: List[LineSegment], yoko: List[LineSegment],
            x0: int, y0: int, x1: int, y1: int):
    if y0 == y1:
        if x0 < x1:
            yoko.append(LineSegment(line, -y0, 0.0, x0, x1))
        elif x0 > x1:
            yoko.append(LineSegment(line, -y0, 0.0, x1, x0))
        return
    if x0 == x1:
        if y0 < y1:
            tate.append(LineSegment(line, x0, math.pi / 2, y0, y1))
        else:
            tate.append(LineSegment(line, x0, math.pi / 2, y1, y0))
        return
    dist = (x0 * y1 - x1 * y0) / math.hypot(x0 - x1, y0 - y1)
    angle = math.atan2(y1 - y0, x1 - x0)
    if -_d45 < angle < _d45:
        yoko.append(LineSegment(line, dist, angle, x0, x1))
        return
    if angle > 0:
        tate.append(LineSegment(line, dist, angle, y0, y1))
    else:
        tate.append(LineSegment(line, dist, angle + math.pi, y1, y0))


def ineighbors(iterable):
    iterator = iter(iterable)
    try:
        p = next(iterator)
        while True:
            n = next(iterator)
            yield (p, n)
            p = n
    except StopIteration:
        return


class DupValidator(Validator):

    name = "dup"

    filters = {
        "alias": {False},
        "category": default_filters["category"] - {"user-owned"},
        "transform": {False},
    }

    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        exact_only = not isKanji(name)

        tate: List[LineSegment] = []
        yoko: List[LineSegment] = []
        curve: List[Tuple[KageLine, List[int]]] = []
        curve2: List[KageLine] = []
        buhin: List[KageLine] = []
        buhinIchi: List[KageLine] = []

        for line in kage.lines:
            stype = line.stroke_type
            coords = line.coords
            if stype == 0:
                pass
            elif stype == 1:
                addLine(line, tate, yoko, *coords[0], *coords[1])
            elif stype == 2:
                curve.append((line, [*coords[0], *coords[1], *coords[2]]))
            elif stype in (3, 4):
                addLine(line, tate, yoko, *coords[0], *coords[1])
                addLine(line, tate, yoko, *coords[1], *coords[2])
            elif stype == 6:
                curve2.append(line)
            elif stype == 7:
                addLine(line, tate, yoko, *coords[0], *coords[1])
                curve.append((line, [*coords[1], *coords[2], *coords[3]]))
            elif stype == 9:
                buhinIchi.append(line)
            elif stype == 99:
                buhin.append(line)

        yoko_thresh = 0 if exact_only else 4
        yoko.sort(key=lambda r: r.dist)
        for i, yoko1 in enumerate(yoko):
            for yoko2 in yoko[i + 1:]:
                if yoko2.dist - yoko1.dist > yoko_thresh:
                    break
                if abs(yoko1.angle - yoko2.angle) > 1.0 / 60.0:
                    continue
                if yoko2.t0 <= yoko1.t1 and yoko1.t0 <= yoko2.t1:
                    return [
                        error_codes.HORILINE,
                        [yoko1.line.line_number, yoko1.line.strdata],
                        [yoko2.line.line_number, yoko2.line.strdata],
                        min(yoko1.t1 - yoko2.t0, yoko2.t1 - yoko1.t0,
                            yoko1.t1 - yoko1.t0, yoko2.t1 - yoko2.t0)
                    ]  # 横

        tate_thresh = 0 if exact_only else 9
        tate.sort(key=lambda r: r.dist)
        for i, tate1 in enumerate(tate):
            for tate2 in tate[i + 1:]:
                if tate2.dist - tate1.dist > tate_thresh:
                    break
                if abs(tate1.angle - tate2.angle) > 1.0 / 60.0:
                    continue
                if tate2.t0 < tate1.t1 and tate1.t0 < tate2.t1:
                    return [
                        error_codes.VERTLINE,
                        [tate1.line.line_number, tate1.line.strdata],
                        [tate2.line.line_number, tate2.line.strdata],
                        min(tate1.t1 - tate2.t0, tate2.t1 - tate1.t0,
                            tate1.t1 - tate1.t0, tate2.t1 - tate2.t0)
                    ]  # 縦

        thresh = 0 if exact_only else 3
        curve.sort(key=lambda line_coords: line_coords[1][0])
        for (curve_1, curve_1_coords), (curve_2, curve_2_coords) in \
                ineighbors(curve):
            if all(-thresh <= curve_1_coords[j] - curve_2_coords[j] <= thresh
                   for j in range(6)):
                return [
                    error_codes.CURVE,
                    [curve_1.line_number, curve_1.strdata],
                    [curve_2.line_number, curve_2.strdata]
                ]  # 曲線

        curve2.sort(key=lambda line: line.coords[0][0])
        for curve21, curve22 in ineighbors(curve2):
            if all(-thresh <= curve21.data[j] - curve22.data[j] <= thresh
                   for j in range(3, 11)):
                return [
                    error_codes.CCURVE,
                    [curve21.line_number, curve21.strdata],
                    [curve22.line_number, curve22.strdata]
                ]  # 複曲線

        buhin.sort(key=lambda line: line.coords[0][0])
        for buhin1, buhin2 in ineighbors(buhin):
            if buhin1.part_name != buhin2.part_name:
                continue
            if all(-thresh <= buhin1.data[j] - buhin2.data[j] <= thresh
                   for j in range(3, 7)):
                return [
                    error_codes.PART,
                    [buhin1.line_number, buhin1.strdata],
                    [buhin2.line_number, buhin2.strdata]
                ]  # 部品

        buhinIchi.sort(key=lambda line: line.coords[0][0])
        for buhinIchi1, buhinIchi2 in ineighbors(buhinIchi):
            if all(-thresh <= buhinIchi1.data[j] - buhinIchi2.data[j] <= thresh
                   for j in range(3, 7)):
                return [
                    error_codes.PARTPOS,
                    [buhinIchi1.line_number, buhinIchi1.strdata],
                    [buhinIchi2.line_number, buhinIchi2.strdata]
                ]  # 部品位置

        return False
