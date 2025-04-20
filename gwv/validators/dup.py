from __future__ import annotations

import itertools
import math
import operator
from typing import TYPE_CHECKING, NamedTuple, TypeVar

from gwv import filters
from gwv.validators import SingleErrorValidator, ValidatorErrorEnum, error_code

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from gwv.kagedata import KageLine
    from gwv.validatorctx import ValidatorContext


class DupError(NamedTuple):
    line1: KageLine
    line2: KageLine


class DupErrorAmount(NamedTuple):
    line1: KageLine
    line2: KageLine
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


def addLine(
    line: KageLine,
    tate: list[LineSegment],
    yoko: list[LineSegment],
    x0: int,
    y0: int,
    x1: int,
    y1: int,
):
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


def dup_line_segments(segments: list[LineSegment], thresh: float, inclusive: bool):
    comp_op = operator.le if inclusive else operator.lt
    segments.sort(key=lambda r: r.dist)
    for i, seg1 in enumerate(segments):
        for seg2 in segments[i + 1 :]:
            if seg2.dist - seg1.dist > thresh:
                break
            if abs(seg1.angle - seg2.angle) > 1.0 / 60.0:
                continue
            if comp_op(seg2.t0, seg1.t1) and comp_op(seg1.t0, seg2.t1):
                amount = min(
                    seg1.t1 - seg2.t0,
                    seg2.t1 - seg1.t0,
                    seg1.t1 - seg1.t0,
                    seg2.t1 - seg2.t0,
                )
                return (seg1, seg2, amount)
    return None


T = TypeVar("T")


def ineighbors(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
    iterator = iter(iterable)
    try:
        p = next(iterator)
        while True:
            n = next(iterator)
            yield (p, n)
            p = n
    except StopIteration:
        return


def dup_coords(elems: list[tuple[KageLine, list[int]]], thresh: int):
    elems.sort(key=lambda elem: elem[1][0])
    for (line1, coords1), (line2, coords2) in ineighbors(elems):
        if all(
            abs(coord1 - coord2) <= thresh for coord1, coord2 in zip(coords1, coords2)
        ):
            return (line1, line2)
    return None


class DupValidator(SingleErrorValidator):
    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    @filters.check_only(-filters.has_transform)
    def is_invalid(self, ctx: ValidatorContext):
        exact_only = ctx.is_hikanji

        tate: list[LineSegment] = []
        yoko: list[LineSegment] = []
        curve: list[tuple[KageLine, list[int]]] = []
        curve2: list[tuple[KageLine, list[int]]] = []
        buhin: dict[str, list[tuple[KageLine, list[int]]]] = {}
        buhinIchi: list[tuple[KageLine, list[int]]] = []

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
                buhin.setdefault(line.part_name, []).append(
                    (line, list(itertools.chain(*coords)))
                )

        yoko_thresh = 0.0 if exact_only else 4.0
        if param := dup_line_segments(yoko, yoko_thresh, True):
            yoko1, yoko2, amount = param
            return E.HORILINE(yoko1.line, yoko2.line, amount)

        tate_thresh = 0.0 if exact_only else 9.0
        if param := dup_line_segments(tate, tate_thresh, False):
            tate1, tate2, amount = param
            return E.VERTLINE(tate1.line, tate2.line, amount)

        thresh = 0 if exact_only else 3

        if line12 := dup_coords(curve, thresh):
            return E.CURVE(*line12)

        if line12 := dup_coords(curve2, thresh):
            return E.CCURVE(*line12)

        for buhin_sub in buhin.values():
            if line12 := dup_coords(buhin_sub, thresh):
                return E.PART(*line12)

        if line12 := dup_coords(buhinIchi, thresh):
            return E.PARTPOS(*line12)

        return False
