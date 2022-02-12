import itertools
import math
from typing import Iterable, Iterator, List, NamedTuple, Tuple, TypeVar

import gwv.filters as filters
from gwv.kagedata import KageLine
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class DupError(NamedTuple):
    line1: list  # kage line number and data
    line2: list  # kage line number and data


class DupErrorAmount(NamedTuple):
    line1: list  # kage line number and data
    line2: list  # kage line number and data
    amount: float


class DupValidatorError(ValidatorErrorEnum):
    @error_code("10")
    class HORILINE(DupErrorAmount):
        """横"""
    @error_code("11")
    class VERTLINE(DupErrorAmount):
        """縦"""
    @error_code("2")
    class CURVE(DupError):
        """曲線"""
    @error_code("3")
    class CCURVE(DupError):
        """複曲線"""
    @error_code("99")
    class PART(DupError):
        """部品"""
    @error_code("9")
    class PARTPOS(DupError):
        """部品位置"""


E = DupValidatorError


_d45 = math.pi / 4.0


class LineSegment(NamedTuple):
    line: KageLine
    dist: float  # (0, 0)と直線との距離
    angle: float  # yoko: -pi/4 < theta < pi/4; tate: 0 < theta < pi
    t0: int
    t1: int


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


T = TypeVar("T")


def ineighbors(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
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

    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    @filters.check_only(-filters.has_transform)
    def is_invalid(self, ctx: ValidatorContext):
        exact_only = ctx.is_hikanji

        tate: List[LineSegment] = []
        yoko: List[LineSegment] = []
        curve: List[Tuple[KageLine, List[int]]] = []
        curve2: List[Tuple[KageLine, List[int]]] = []
        buhin: List[Tuple[KageLine, List[int]]] = []
        buhinIchi: List[Tuple[KageLine, List[int]]] = []

        for line in ctx.glyph.kage.lines:
            stype = line.stroke_type
            coords = line.coords
            if coords is None:
                continue
            if stype == 0:
                pass
            elif stype == 1:
                addLine(line, tate, yoko, *coords[0], *coords[1])
            elif stype == 2:
                curve.append((line, list(itertools.chain(*coords[0:3]))))
            elif stype in (3, 4):
                addLine(line, tate, yoko, *coords[0], *coords[1])
                addLine(line, tate, yoko, *coords[1], *coords[2])
            elif stype == 6:
                curve2.append((line, list(itertools.chain(*coords[0:4]))))
            elif stype == 7:
                addLine(line, tate, yoko, *coords[0], *coords[1])
                curve.append((line, list(itertools.chain(*coords[1:4]))))
            elif stype == 9:
                buhinIchi.append((line, list(itertools.chain(*coords[0:2]))))
            elif stype == 99:
                buhin.append((line, list(itertools.chain(*coords))))

        yoko_thresh = 0 if exact_only else 4
        yoko.sort(key=lambda r: r.dist)
        for i, yoko1 in enumerate(yoko):
            for yoko2 in yoko[i + 1:]:
                if yoko2.dist - yoko1.dist > yoko_thresh:
                    break
                if abs(yoko1.angle - yoko2.angle) > 1.0 / 60.0:
                    continue
                if yoko2.t0 <= yoko1.t1 and yoko1.t0 <= yoko2.t1:
                    return E.HORILINE(
                        [yoko1.line.line_number, yoko1.line.strdata],
                        [yoko2.line.line_number, yoko2.line.strdata],
                        min(yoko1.t1 - yoko2.t0, yoko2.t1 - yoko1.t0,
                            yoko1.t1 - yoko1.t0, yoko2.t1 - yoko2.t0)
                    )  # 横

        tate_thresh = 0 if exact_only else 9
        tate.sort(key=lambda r: r.dist)
        for i, tate1 in enumerate(tate):
            for tate2 in tate[i + 1:]:
                if tate2.dist - tate1.dist > tate_thresh:
                    break
                if abs(tate1.angle - tate2.angle) > 1.0 / 60.0:
                    continue
                if tate2.t0 < tate1.t1 and tate1.t0 < tate2.t1:
                    return E.VERTLINE(
                        [tate1.line.line_number, tate1.line.strdata],
                        [tate2.line.line_number, tate2.line.strdata],
                        min(tate1.t1 - tate2.t0, tate2.t1 - tate1.t0,
                            tate1.t1 - tate1.t0, tate2.t1 - tate2.t0)
                    )  # 縦

        thresh = 0 if exact_only else 3
        curve.sort(key=lambda line_coords: line_coords[1][0])
        for (curve_1, curve_1_coords), (curve_2, curve_2_coords) in \
                ineighbors(curve):
            if all(abs(coord1 - coord2) <= thresh
                   for coord1, coord2 in zip(curve_1_coords, curve_2_coords)):
                return E.CURVE(
                    [curve_1.line_number, curve_1.strdata],
                    [curve_2.line_number, curve_2.strdata]
                )  # 曲線

        curve2.sort(key=lambda line_coords: line_coords[1][0])
        for (curve21, curve21_coords), (curve22, curve22_coords) in \
                ineighbors(curve2):
            if all(abs(coord1 - coord2) <= thresh
                   for coord1, coord2 in zip(curve21_coords, curve22_coords)):
                return E.CCURVE(
                    [curve21.line_number, curve21.strdata],
                    [curve22.line_number, curve22.strdata]
                )  # 複曲線

        buhin.sort(key=lambda line_coords: line_coords[1][0])
        for (buhin1, buhin1_coords), (buhin2, buhin2_coords) in \
                ineighbors(buhin):
            if buhin1.part_name != buhin2.part_name:
                continue
            if all(abs(coord1 - coord2) <= thresh
                   for coord1, coord2 in zip(buhin1_coords, buhin2_coords)):
                return E.PART(
                    [buhin1.line_number, buhin1.strdata],
                    [buhin2.line_number, buhin2.strdata]
                )  # 部品

        buhinIchi.sort(key=lambda line_coords: line_coords[1][0])
        for (buhinIchi1, buhinIchi1_coords), (buhinIchi2, buhinIchi2_coords) \
                in ineighbors(buhinIchi):
            if all(abs(coord1 - coord2) <= thresh
                   for coord1, coord2 in
                   zip(buhinIchi1_coords, buhinIchi2_coords)):
                return E.PARTPOS(
                    [buhinIchi1.line_number, buhinIchi1.strdata],
                    [buhinIchi2.line_number, buhinIchi2.strdata]
                )  # 部品位置

        return False
