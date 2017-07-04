# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from gwv.kagedata import KageData
from gwv.validators import Validator
from gwv.validators import ErrorCodes

error_codes = ErrorCodes(
    FIRST_PART_TB_IN_LR_IDS="1",  # 左右のIDSだが最初が上下の部品
    FIRST_PART_RIGHT_IN_LR_IDS="2",  # 左右のIDSだが右部品が最初
    LEFT_PART_NOT_FIRST_IN_LR_IDS="3",  # 左右のIDSだが左の字が最初でない
    FIRST_PART_LANDSCAPE_IN_LR_IDS="6",  # 左右のIDSだが最初の部品が横長の配置
    FIRST_PART_LR_IN_TB_IDS="10",  # 上下のIDSだが最初が左右の部品
    FIRST_PART_BOTTOM_IN_TB_IDS="12",  # 上下のIDSだが下部品が最初
    TOP_PART_NOT_FIRST_IN_TB_IDS="13",  # 上下のIDSだが上の字が最初でない
    FIRST_PART_PORTRAIT_IN_TB_IDS="15",  # 上下のIDSだが最初の部品が縦長の配置
    FIRST_PART_INNER_IN_SURROUND_IDS="22",  # 囲むIDSだが内側部品が最初
    OUTER_PART_NOT_FIRST_IN_SURROUND_IDS="23",  # 囲むIDSだが外の字が最初でない
    FIRST_PART_NOT_FIRST_IN_OVERLAP_IDS="33",  # 重ねIDSだが最初の字が最初でない
    UNKNOWN_IDC="90",  # 未定義のIDC
)

filters = {
    "alias": {True, False},
    "category": {"ids"}
}


_re_idc = re.compile(r"^u2ff[\dab]$")
_re_vars = re.compile(r"-([gtvhmi]|k[pv]?|us?|j[asv]?)?(\d{2})(-(var|itaiji)-\d{3})?(@|$)")


def indexOfFirstKanjiBuhinLine(sname, kage):
    """IDSの最初の漢字を部品としているKageLine（なければNone）を返す"""
    for i, sname_i in enumerate(sname):
        if _re_idc.match(sname_i):
            continue
        firstKanji = sname_i
        if firstKanji == "cdp":
            firstKanji += "-" + sname[i + 1]
        for line in kage.lines:
            if line.data[0] == 99 and line.data[7].startswith(firstKanji):
                return line
        return None
    return None


class IdsValidator(Validator):

    name = "ids"

    def is_invalid(self, name, related, kage, gdata, dump):
        # Replace with the entity if the glyph is an alias
        if kage.isAlias():
            r = dump.get(gdata[19:].split("@")[0], None)
            if r:
                gdata = r[1]
                kage = KageData(gdata)

        if not (kage.lines[0].data[0] == 99 and kage.len > 1):
            return False
        fData = kage.lines[0].data
        if fData[4] == fData[6]:
            aspect = float("inf")
        else:
            aspect = abs(float(fData[3] - fData[5]) / (fData[4] - fData[6]))  # x/y

        sname = name.split("-")

        # ⿰⿱ とか ⿱⿰ とかで始まるものは最初の部品の縦横比を予測できない
        isComplicated = (sname[1] in ("u2ff0", "u2ff2") and sname[0] in ("u2ff1", "u2ff3")) or \
                        (sname[1] in ("u2ff1", "u2ff3") and sname[0] in ("u2ff0", "u2ff2"))

        m = _re_vars.search(fData[7])
        if m:
            firstBuhinType = m.group(2)  # 偏化変形接尾コード
        else:
            firstBuhinType = None
        if sname[0] in ("u2ff0", "u2ff2"):
            # [-01] + [-02] or [-01] + [-01] + [-02]
            if firstBuhinType in ("03", "04", "09", "14", "24") and fData[5] - fData[3] > 175.0:
                return [error_codes.FIRST_PART_TB_IN_LR_IDS, fData[7]]  # 左右のIDSだが最初が上下の部品
            if firstBuhinType == "02":
                return [error_codes.FIRST_PART_RIGHT_IN_LR_IDS, fData[7]]  # 左右のIDSだが右部品が最初
            if not isComplicated and firstBuhinType not in ("01", "08") and aspect > 1.8:
                return [error_codes.FIRST_PART_LANDSCAPE_IN_LR_IDS, [0, kage.lines[0].strdata]]  # 左右のIDSだが最初の部品が横長の配置
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                return [error_codes.LEFT_PART_NOT_FIRST_IN_LR_IDS, [fkline.line_number, fkline.strdata]]  # 左右のIDSだが左の字が最初でない
        elif sname[0] in ("u2ff1", "u2ff3"):
            # [-03] + [-04] or [-03] + [-03] + [-04]
            if firstBuhinType in ("01", "02", "08") and fData[6] - fData[4] > 175.0:
                return [error_codes.FIRST_PART_LR_IN_TB_IDS, fData[7]]  # 上下のIDSだが最初が左右の部品
            if firstBuhinType in ("04", "14", "24"):
                return [error_codes.FIRST_PART_BOTTOM_IN_TB_IDS, fData[7]]  # 上下のIDSだが下部品が最初
            if not isComplicated and firstBuhinType not in ("03", "09") and aspect < 0.65:
                return [error_codes.FIRST_PART_PORTRAIT_IN_TB_IDS, [0, kage.lines[0].strdata]]  # 上下のIDSだが最初の部品が縦長の配置
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                return [error_codes.TOP_PART_NOT_FIRST_IN_TB_IDS, [fkline.line_number, fkline.strdata]]  # 上下のIDSだが上の字が最初でない
        elif sname[0] in ("u2ff4", "u2ff5", "u2ff6", "u2ff7", "u2ff8", "u2ff9", "u2ffa"):
            # [-05] + [-06]
            if firstBuhinType in ("02", "06", "07"):
                return [error_codes.FIRST_PART_INNER_IN_SURROUND_IDS, fData[7]]  # 囲むIDSだが内側部品が最初
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                return [error_codes.OUTER_PART_NOT_FIRST_IN_SURROUND_IDS, [fkline.line_number, fkline.strdata]]  # 囲みIDSだが外の字が最初でない
        elif sname[0] == "u2ffb":
            fkline = indexOfFirstKanjiBuhinLine(sname, kage)
            if fkline is not None and fkline.line_number != 0:
                return [error_codes.FIRST_PART_NOT_FIRST_IN_OVERLAP_IDS, [fkline.line_number, fkline.strdata]]  # 重ねIDSだがIDSで最初の字が最初でない
        else:
            return [error_codes.UNKNOWN_IDC, sname[0]]  # 未定義のIDC


validator_class = IdsValidator
