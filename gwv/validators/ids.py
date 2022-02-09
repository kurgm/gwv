import re
from typing import List, NamedTuple, Optional

import gwv.filters as filters
from gwv.helper import RE_REGIONS
from gwv.kagedata import KageData
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class IdsErrorBeginningWrongTypePart(NamedTuple):
    part_name: str


class IdsErrorFirstNotBeginning(NamedTuple):
    middle_line: list  # kage line number and data


class IdsErrorBeginningWrongAspectPart(NamedTuple):
    first_line: list  # kage line number and data


class IdsValidatorError(ValidatorErrorEnum):
    @error_code("1")
    class FIRST_PART_TB_IN_LR_IDS(IdsErrorBeginningWrongTypePart):
        """左右のIDSだが最初が上下の部品"""
    @error_code("2")
    class FIRST_PART_RIGHT_IN_LR_IDS(IdsErrorBeginningWrongTypePart):
        """左右のIDSだが右部品が最初"""
    @error_code("3")
    class LEFT_PART_NOT_FIRST_IN_LR_IDS(IdsErrorFirstNotBeginning):
        """左右のIDSだが左の字が最初でない"""
    @error_code("6")
    class FIRST_PART_LANDSCAPE_IN_LR_IDS(IdsErrorBeginningWrongAspectPart):
        """左右のIDSだが最初の部品が横長の配置"""
    @error_code("10")
    class FIRST_PART_LR_IN_TB_IDS(IdsErrorBeginningWrongTypePart):
        """上下のIDSだが最初が左右の部品"""
    @error_code("12")
    class FIRST_PART_BOTTOM_IN_TB_IDS(IdsErrorBeginningWrongTypePart):
        """上下のIDSだが下部品が最初"""
    @error_code("13")
    class TOP_PART_NOT_FIRST_IN_TB_IDS(IdsErrorFirstNotBeginning):
        """上下のIDSだが上の字が最初でない"""
    @error_code("15")
    class FIRST_PART_PORTRAIT_IN_TB_IDS(IdsErrorBeginningWrongAspectPart):
        """上下のIDSだが最初の部品が縦長の配置"""
    @error_code("22")
    class FIRST_PART_INNER_IN_SURROUND_IDS(IdsErrorBeginningWrongTypePart):
        """囲むIDSだが内側部品が最初"""
    @error_code("23")
    class OUTER_PART_NOT_FIRST_IN_SURROUND_IDS(IdsErrorFirstNotBeginning):
        """囲むIDSだが外の字が最初でない"""
    @error_code("33")
    class FIRST_PART_NOT_FIRST_IN_OVERLAP_IDS(IdsErrorFirstNotBeginning):
        """重ねIDSだが最初の字が最初でない"""
    @error_code("90")
    class UNKNOWN_IDC(NamedTuple):
        """未定義のIDC"""
        idc: str


E = IdsValidatorError


_re_idc = re.compile(r"u2ff[\dab]")
_re_vars = re.compile(
    r"-" + RE_REGIONS + r"?(\d{2})(?:-(?:var|itaiji)-\d{3})?(?=@|$)")


def indexOfFirstKanjiBuhinLine(sname: List[str], kage: KageData):
    """IDSの最初の漢字を部品としているKageLine（なければNone）を返す"""
    for i, sname_i in enumerate(sname):
        if _re_idc.fullmatch(sname_i):
            continue
        firstKanji = sname_i
        if firstKanji == "cdp":
            firstKanji += "-" + sname[i + 1]
        for line in kage.lines:
            if line.stroke_type == 99 and \
                    line.part_name.startswith(firstKanji):
                return line
        return None
    return None


class IdsValidator(Validator):

    @filters.check_only(+filters.is_of_category({"ids"}))
    def is_invalid(self, ctx: ValidatorContext):
        kage = ctx.entity.kage

        if not (kage.lines[0].stroke_type == 99 and kage.len > 1):
            return False
        (x1, y1), (x2, y2) = kage.lines[0].coords
        f_part_name = kage.lines[0].part_name
        if y1 == y2:
            aspect = float("inf")
        else:
            aspect = abs(float(x1 - x2) / (y1 - y2))

        sname = ctx.glyph.name.split("-")

        # ⿰⿱ とか ⿱⿰ とかで始まるものは最初の部品の縦横比を予測できない
        isComplicated = (
            (sname[1] in ("u2ff0", "u2ff2") and sname[0] in ("u2ff1", "u2ff3"))
            or
            (sname[1] in ("u2ff1", "u2ff3") and sname[0] in ("u2ff0", "u2ff2"))
        )

        m = _re_vars.search(f_part_name)
        if m:
            firstBuhinType: Optional[str] = m.group(1)  # 偏化変形接尾コード
        else:
            firstBuhinType = None
        if sname[0] in ("u2ff0", "u2ff2"):
            # [-01] + [-02] or [-01] + [-01] + [-02]
            if firstBuhinType in ("03", "04", "09", "14", "24") and \
                    x2 - x1 > 175.0:
                # 左右のIDSだが最初が上下の部品
                return E.FIRST_PART_TB_IN_LR_IDS(f_part_name)
            if firstBuhinType == "02":
                # 左右のIDSだが右部品が最初
                return E.FIRST_PART_RIGHT_IN_LR_IDS(f_part_name)
            if not isComplicated and firstBuhinType not in ("01", "08") and \
                    aspect > 1.8:
                # 左右のIDSだが最初の部品が横長の配置
                return E.FIRST_PART_LANDSCAPE_IN_LR_IDS(
                    [0, kage.lines[0].strdata])
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                # 左右のIDSだが左の字が最初でない
                return E.LEFT_PART_NOT_FIRST_IN_LR_IDS(
                    [fkline.line_number, fkline.strdata])
        elif sname[0] in ("u2ff1", "u2ff3"):
            # [-03] + [-04] or [-03] + [-03] + [-04]
            if firstBuhinType in ("01", "02", "08") and \
                    y2 - y1 > 175.0:
                # 上下のIDSだが最初が左右の部品
                return E.FIRST_PART_LR_IN_TB_IDS(f_part_name)
            if firstBuhinType in ("04", "14", "24"):
                # 上下のIDSだが下部品が最初
                return E.FIRST_PART_BOTTOM_IN_TB_IDS(f_part_name)
            if not isComplicated and firstBuhinType not in ("03", "09") and \
                    aspect < 0.65:
                # 上下のIDSだが最初の部品が縦長の配置
                return E.FIRST_PART_PORTRAIT_IN_TB_IDS(
                    [0, kage.lines[0].strdata])
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                # 上下のIDSだが上の字が最初でない
                return E.TOP_PART_NOT_FIRST_IN_TB_IDS(
                    [fkline.line_number, fkline.strdata])
        elif sname[0] in (
                "u2ff4", "u2ff5", "u2ff6", "u2ff7", "u2ff8", "u2ff9", "u2ffa"):
            # [-05] + [-06]
            if firstBuhinType in ("02", "06", "07"):
                # 囲むIDSだが内側部品が最初
                return E.FIRST_PART_INNER_IN_SURROUND_IDS(f_part_name)
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                # 囲みIDSだが外の字が最初でない
                return E.OUTER_PART_NOT_FIRST_IN_SURROUND_IDS(
                    [fkline.line_number, fkline.strdata])
        elif sname[0] == "u2ffb":
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                # 重ねIDSだがIDSで最初の字が最初でない
                return E.FIRST_PART_NOT_FIRST_IN_OVERLAP_IDS(
                    [fkline.line_number, fkline.strdata])
        else:
            return E.UNKNOWN_IDC(sname[0])  # 未定義のIDC

        return False
