import re
from typing import Dict, Tuple, Union

from gwv.dump import Dump
import gwv.filters as filters
from gwv.helper import GWGroupLazyLoader
from gwv.helper import RE_REGIONS
from gwv.kagedata import KageData
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    # グループ:NonSpacingGlyphs-Halfwidthに含まれているが全角
    INCORRECT_NONSPACINGGLYPHS_HALFWIDTH="0",
    # グループ:HalfwidthGlyphs-{BMP,SMP,nonUCS}に含まれているが全角
    INCORRECT_HALFWIDTHGLYPHS="1",
    # 半角だがグループ:HalfwidthGlyphs-{BMP,SMP,nonUCS}に含まれていない
    INCORRECT_FULLWIDTHGLYPHS="2",
)


_re_halfWidth = re.compile(
    r"-halfwidth$|^uff(6[1-9a-f]|[7-9a-d][0-9a-f]|e[8-e])$")
_re_fullWidth = re.compile(r"-fullwidth$|^uff([0-5][0-9a-f]|60|e[0-6])$")
_re_hen = re.compile(r"-" + RE_REGIONS + r"?01(-(var|itaiji)-|$)")


halflists = [
    GWGroupLazyLoader("HalfwidthGlyphs-BMP", isset=True),
    GWGroupLazyLoader("HalfwidthGlyphs-SMP", isset=True),
    GWGroupLazyLoader("HalfwidthGlyphs-nonUCS", isset=True),
]
nonspacinghalflist = GWGroupLazyLoader(
    "NonSpacingGlyphs-Halfwidth", isset=True)


def getDWidth(glyphname: str):
    if glyphname in nonspacinghalflist.get_data():
        return 0
    for halflist in halflists:
        if glyphname in halflist.get_data():
            return 1
    return 2


pinf = float("inf")
ninf = -pinf

buhinWidths: Dict[str, Tuple[float, float]] = {
    "left-half-circle": (15.0, 100.0),  # @1
    "right-half-circle": (100.0, 185.0),  # @1
    "palatal-hook": (40.0, 64.0),  # @1
    "short-backslash": (94.0, 110.0),  # @1
    "short-slash": (89.0, 105.0),  # @1
    "small-diamond": (76.0, 124.0),  # @1
    "vertical-short-bar": (99.0, 102.0),  # @1
    "u002c": (36.0, 56.0),  # @5 COMMA
    "u002e": (44.0, 56.0),  # @4 FULL STOP
    "u0049": (30.0, 70.0),  # @4 LATIN CAPITAL LETTER I
    "u006a": (9.0, 56.0),  # @13 LATIN SMALL LETTER J
    "u006c": (30.0, 70.0),  # @5 LATIN SMALL LETTER L
    "u02d9": (44.0, 56.0),  # @6 DOT ABOVE
    "u02db": (49.0, 79.0),  # @4 OGONEK
    "u026a": (30.0, 70.0),  # @5 LATIN LETTER SMALL CAPITAL I
    "u0020-u0309": (41.0, 63.0),  # @2 SPACE, COMBINING HOOK ABOVE
    "u0020-u0323": (44.0, 56.0),  # @3 SPACE, COMBINING DOT BELOW
    "u16c1": (50.0, 50.0),  # @3 RUNIC LETTER ISAZ IS ISS I
    "u2019": (36.0, 56.0),  # @4 RIGHT SINGLE QUOTATION MARK
    "u2032": (40.0, 60.0),  # @7 PRIME
    "u25e6": (33.0, 67.0),  # @1 WHITE BULLET
    "u25e6-fullwidth": (83.0, 117.0),  # @2
    "u26ac": (62.4, 137.6),  # @1 MEDIUM SMALL WHITE CIRCLE
    "u30fb": (92.0, 108.0),  # @2 KATAKANA MIDDLE DOT
}


class WidthValidator(Validator):

    name = "width"

    @filters.check_only(+filters.is_of_category({
        "user-owned", "ucs-hikanji", "ucs-hikanji-var", "toki", "other"}))
    @filters.check_only(-filters.has_transform)
    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        minX: Union[int, float]
        maxX: Union[int, float]
        if _re_fullWidth.search(name):
            minX = 0
            maxX = 200
        elif _re_halfWidth.search(name):
            minX = 0
            maxX = 100
        elif _re_hen.search(name):
            minX = 0
            maxX = 200
        else:
            minX = pinf
            maxX = ninf
            for line in kage.lines:
                if line.stroke_type == 0:
                    continue
                if line.stroke_type != 99:
                    xs = [x for x, _y in line.coords if x is not None]
                    if xs:
                        minX = min(minX, *xs)
                        maxX = max(maxX, *xs)
                else:
                    (xL, _yL), (xR, _yR) = line.coords
                    w = xR - xL
                    gn: str = line.part_name.split("@")[0]
                    if gn in buhinWidths:
                        bb = buhinWidths[gn]
                        bL = xL + w * bb[0] / 200.0
                        bR = xL + w * bb[1] / 200.0
                    else:
                        bgW = getDWidth(gn)
                        if bgW == 0:
                            bL = minX
                            bR = maxX
                        elif bgW == 2:
                            if _re_fullWidth.search(gn) or \
                                    (gn + "-halfwidth") in dump:
                                bL = xL + w * 0.31
                                bR = xL + w * 0.69
                            else:
                                bL = xL + w * 0.06
                                bR = xL + w * 0.94
                        else:
                            bL = xL + w * 0.06
                            bR = xL + w * 0.44
                    minX = min(minX, bL, bR)
                    maxX = max(maxX, bL, bR)
        if maxX == ninf:
            return False
        gWidth = getDWidth(name)
        if (maxX <= 110 and minX < 90) is not (gWidth != 2):
            return [str(gWidth)]
        return False
