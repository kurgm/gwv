import math

from gwv.helper import isYoko
from gwv.validators import filters as default_filters
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

    filters = {
        "alias": {False},
        "category": default_filters["category"] - {"user-owned"}
    }

    def is_invalid(self, name, related, kage, gdata, dump):
        for line in kage.lines:
            data = line.data
            stype = data[0]
            if stype == 1:
                xDif = abs(data[3] - data[5])
                yDif = abs(data[4] - data[6])
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
                xDif1 = abs(data[3] - data[5])
                yDif1 = abs(data[4] - data[6])
                if xDif1 != 0 and xDif1 <= 3:
                    # 折れの前半が歪んだ垂直
                    return [
                        error_codes.SKEWED_VERT_ORE_FIRST,
                        [line.line_number, line.strdata],
                        round(math.atan2(xDif1, yDif1) * 180 / math.pi, 1)]
                xDif2 = abs(data[5] - data[7])
                yDif2 = abs(data[6] - data[8])
                if yDif2 != 0 and yDif2 <= 3:
                    # 折れの後半が歪んだ水平
                    return [
                        error_codes.SKEWED_HORI_ORE_LAST,
                        [line.line_number, line.strdata],
                        round(math.atan2(yDif2, xDif2) * 180 / math.pi, 1)]
            elif stype == 4:
                xDif = abs(data[5] - data[7])
                yDif = abs(data[6] - data[8])
                if yDif != 0 and yDif <= 3:
                    # 乙の後半が歪んだ水平
                    return [
                        error_codes.SKEWED_HORI_OTSU_LAST,
                        [line.line_number, line.strdata],
                        round(math.atan2(yDif, xDif) * 180 / math.pi, 1)]
            elif stype == 7:
                if isYoko(*data[3:7]):
                    # 縦払いの直線部分が横
                    return [
                        error_codes.HORI_TATEBARAI_FIRST,
                        [line.line_number, line.strdata]]
                xDif1 = data[5] - data[3]
                yDif1 = data[6] - data[4]
                theta1 = math.atan2(yDif1, xDif1)
                if xDif1 == 0 and yDif1 == 0:
                    theta1 = math.pi / 2
                xDif2 = data[7] - data[5]
                yDif2 = data[8] - data[6]
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
