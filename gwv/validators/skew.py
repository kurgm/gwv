import math

import gwv.filters as filters
from gwv.helper import isYoko
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    SKEWED_HORI_LINE="10",  # 歪んだ水平
    SKEWED_VERT_LINE="11",  # 歪んだ垂直
    SKEWED_HORI_ORE_LAST="30",  # 折れの後半が歪んだ水平
    SKEWED_VERT_ORE_FIRST="31",  # 折れの前半が歪んだ垂直
    SKEWED_HORI_OTSU_LAST="40",  # 乙の後半が歪んだ水平
    HORI_TATEBARAI_FIRST="70",  # 縦払いの直線部分が横
    SNAPPED_TATEBARAI="71",  # 曲がった縦払い
    SKEWED_VERT_TATEBARAI_FIRST="72",  # 縦払いの直線部分が歪んだ垂直
)


class SkewValidator(Validator):

    name = "skew"

    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            stype = line.stroke_type
            coords = line.coords
            if stype == 1:
                xDif = abs(coords[0][0] - coords[1][0])
                yDif = abs(coords[0][1] - coords[1][1])
                if xDif <= yDif and xDif != 0 and xDif <= 3:
                    # 歪んだ垂直
                    return [
                        error_codes.SKEWED_VERT_LINE,
                        [line.line_number, line.strdata],
                        round(math.atan2(xDif, yDif) * 180 / math.pi, 1)]
                if xDif > yDif and yDif != 0 and yDif <= 3:
                    # 歪んだ水平
                    return [
                        error_codes.SKEWED_HORI_LINE,
                        [line.line_number, line.strdata],
                        round(math.atan2(yDif, xDif) * 180 / math.pi, 1)]
            elif stype == 3:
                xDif1 = abs(coords[0][0] - coords[1][0])
                yDif1 = abs(coords[0][1] - coords[1][1])
                if xDif1 != 0 and xDif1 <= 3:
                    # 折れの前半が歪んだ垂直
                    return [
                        error_codes.SKEWED_VERT_ORE_FIRST,
                        [line.line_number, line.strdata],
                        round(math.atan2(xDif1, yDif1) * 180 / math.pi, 1)]
                xDif2 = abs(coords[1][0] - coords[2][0])
                yDif2 = abs(coords[1][1] - coords[2][1])
                if yDif2 != 0 and yDif2 <= 3:
                    # 折れの後半が歪んだ水平
                    return [
                        error_codes.SKEWED_HORI_ORE_LAST,
                        [line.line_number, line.strdata],
                        round(math.atan2(yDif2, xDif2) * 180 / math.pi, 1)]
            elif stype == 4:
                xDif = abs(coords[1][0] - coords[2][0])
                yDif = abs(coords[1][1] - coords[2][1])
                if yDif != 0 and yDif <= 3:
                    # 乙の後半が歪んだ水平
                    return [
                        error_codes.SKEWED_HORI_OTSU_LAST,
                        [line.line_number, line.strdata],
                        round(math.atan2(yDif, xDif) * 180 / math.pi, 1)]
            elif stype == 7:
                if isYoko(*coords[0], *coords[1]):
                    # 縦払いの直線部分が横
                    return [
                        error_codes.HORI_TATEBARAI_FIRST,
                        [line.line_number, line.strdata]]
                xDif1 = coords[1][0] - coords[0][0]
                yDif1 = coords[1][1] - coords[0][1]
                theta1 = math.atan2(yDif1, xDif1)
                if xDif1 == 0 and yDif1 == 0:
                    theta1 = math.pi / 2
                xDif2 = coords[2][0] - coords[1][0]
                yDif2 = coords[2][1] - coords[1][1]
                theta2 = math.atan2(yDif2, xDif2)
                if (xDif1 == 0 and xDif2 != 0) or \
                        abs(theta1 - theta2) * 60 > 3:
                    # 曲がった縦払い
                    return [
                        error_codes.SNAPPED_TATEBARAI,
                        [line.line_number, line.strdata],
                        round(abs(theta1 - theta2) * 180 / math.pi, 1)]
                if xDif1 != 0 and -3 <= xDif1 <= 3:
                    # 縦払いの直線部分が歪んだ垂直
                    return [
                        error_codes.SKEWED_VERT_TATEBARAI_FIRST,
                        [line.line_number, line.strdata],
                        round(abs(90 - theta1 * 180 / math.pi), 1)]
        return False

    def get_result(self):
        for key, val in self.results.items():
            if key != error_codes.HORI_TATEBARAI_FIRST:
                # 歪み角度が大きい順にソート
                val.sort(key=lambda r: r[2], reverse=True)
        return super(SkewValidator, self).get_result()
