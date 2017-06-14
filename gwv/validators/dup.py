# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math

from gwv.validators import filters as default_filters
from gwv.validators import ValidatorClass

filters = {
    "alias": {False},
    "category": default_filters["category"] - {"user-owned"}
}

_d45 = math.pi / 4.0


class LineSegment(object):

    def __init__(self, line, dist, angle, t0, t1):
        self.line = line
        self.dist = dist  # (0, 0)と直線との距離
        self.angle = angle  # yoko: -pi/4 < theta < pi/4; tate: 0 < theta < pi
        self.t0 = t0
        self.t1 = t1


def addLine(line, tate, yoko, x0, y0, x1, y1):
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
    p = iterator.next()
    while True:
        n = iterator.next()
        yield (p, n)
        p = n


class Validator(ValidatorClass):

    name = "dup"

    def is_invalid(self, name, related, kage, gdata, dump):
        tate = []
        yoko = []
        curve = []
        curve2 = []
        buhin = []
        buhinIchi = []

        for line in kage.lines:
            stype = line.data[0]
            if stype == 0:
                pass
            elif stype == 1:
                addLine(line, tate, yoko, *line.data[3:7])
            elif stype == 2:
                curve.append([line, line.data[3:9]])
            elif stype in (3, 4):
                addLine(line, tate, yoko, *line.data[3:7])
                addLine(line, tate, yoko, *line.data[5:9])
            elif stype == 6:
                curve2.append(line)
            elif stype == 7:
                addLine(line, tate, yoko, *line.data[3:7])
                curve.append([line, line.data[5:11]])
            elif stype == 9:
                buhinIchi.append(line)
            elif stype == 99:
                buhin.append(line)

        yoko.sort(key=lambda r: r.dist)
        for i, yoko1 in enumerate(yoko):
            for yoko2 in yoko[i + 1:]:
                if yoko2.dist - yoko1.dist > 4:
                    break
                if abs(yoko1.angle - yoko2.angle) > 1.0 / 60.0:
                    continue
                if yoko2.t0 <= yoko1.t1 and yoko1.t0 <= yoko2.t1:
                    return [
                        10,
                        [yoko1.line.line_number, yoko1.line.strdata],
                        [yoko2.line.line_number, yoko2.line.strdata],
                        min(yoko1.t1 - yoko2.t0, yoko2.t1 - yoko1.t0,
                            yoko1.t1 - yoko1.t0, yoko2.t1 - yoko2.t0)
                    ]  # 横

        tate.sort(key=lambda r: r.dist)
        for i, tate1 in enumerate(tate):
            for tate2 in tate[i + 1:]:
                if tate2.dist - tate1.dist > 9:
                    break
                if abs(tate1.angle - tate2.angle) > 1.0 / 60.0:
                    continue
                if tate2.t0 < tate1.t1 and tate1.t0 < tate2.t1:
                    return [
                        11,
                        [tate1.line.line_number, tate1.line.strdata],
                        [tate2.line.line_number, tate2.line.strdata],
                        min(tate1.t1 - tate2.t0, tate2.t1 - tate1.t0,
                            tate1.t1 - tate1.t0, tate2.t1 - tate2.t0)
                    ]  # 縦

        curve.sort(key=lambda (line, coords): coords[0])
        for (curve_1, curve_1_coords), (curve_2, curve_2_coords) in ineighbors(curve):
            if all(-3 <= curve_1_coords[j] - curve_2_coords[j] <= 3 for j in range(6)):
                return [
                    2,
                    [curve_1.line_number, curve_1.strdata],
                    [curve_2.line_number, curve_2.strdata]
                ]  # 曲線

        curve2.sort(key=lambda line: line.data[3])
        for curve21, curve22 in ineighbors(curve2):
            if all(-3 <= curve21.data[j] - curve22.data[j] <= 3 for j in range(3, 11)):
                return [
                    3,
                    [curve21.line_number, curve21.strdata],
                    [curve22.line_number, curve22.strdata]
                ]  # 複曲線

        buhin.sort(key=lambda line: line.data[3])
        for buhin1, buhin2 in ineighbors(buhin):
            if buhin1.data[7] != buhin2.data[7]:
                continue
            if all(-3 <= buhin1.data[j] - buhin2.data[j] <= 3 for j in range(3, 7)):
                return [
                    99,
                    [buhin1.line_number, buhin1.strdata],
                    [buhin2.line_number, buhin2.strdata]
                ]  # 部品

        buhinIchi.sort(key=lambda line: line.data[3])
        for buhinIchi1, buhinIchi2 in ineighbors(buhinIchi):
            if all(-3 <= buhinIchi1.data[j] - buhinIchi2.data[j] <= 3 for j in range(3, 7)):
                return [
                    9,
                    [buhinIchi1.line_number, buhinIchi1.strdata],
                    [buhinIchi2.line_number, buhinIchi2.strdata]
                ]  # 部品位置
