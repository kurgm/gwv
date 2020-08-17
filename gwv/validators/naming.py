import re

from gwv.helper import GWGroupLazyLoader
from gwv.helper import load_package_data
from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    NAMING_RULE_VIOLATION="0",  # 命名規則違反
    INVALID_IDS="1",  # 不正なIDS
    PROHIBITED_GLYPH_NAME="2",  # 禁止されたグリフ名
    ENCODED_CDP_IN_IDS="3",  # UCSで符号化済みのCDP外字
    DEPRECATED_NAMING_RULE="4",  # 廃止予定の命名規則
)


filters = {
    "alias": {True, False},
    "category": default_filters["category"] - {"user-owned"}
}


class NamingRules(object):

    def __init__(self, data):
        self.regex = [re.compile(regex) for regex in data.get("regex", [])]
        self.string = set(data.get("string", []))

    def match(self, name):
        return name in self.string or any(
            regex.search(name) for regex in self.regex)


def get_naming_rules():
    naming_data = load_package_data("data/naming.yaml")
    return {
        key: NamingRules(value) for key, value in naming_data.items()
    }


def get_cdp_dict():
    it = iter(GWGroupLazyLoader("UCSで符号化されたCDP外字", isset=False).get_data())
    return dict(zip(it, it))


cdp_dict = get_cdp_dict()
rules = get_naming_rules()

_re_var = re.compile(r"-(var|itaiji)-\d{3}$")
_re_henka = re.compile(r"-\d{2}$")

_re_gl_glyph = re.compile(
    r"^(j78|j83|j90|jsp|jx1-200[04]|jx2|k0|g0|c[0-9a-f])-([\da-f]{4})$")
_re_valid_gl = re.compile(r"(2[1-9a-f]|[3-6][\da-f]|7[\da-e]){2}")

_re_cdp = re.compile(r"(?:^|-)(cdp([on]?)-([\da-f]{4}))(?=-|$)")
_re_valid_cdp = re.compile(
    r"(8[1-9a-f]|9[\da-f]|a0|c[67])(a[1-9a-f]|[4-6b-e][\da-f]|[7f][\da-e])")

_re_ids_head = re.compile(r"u2ff[\dab]-")
_re_idc_2 = re.compile(r"(^|-)u2ff[014-9ab](?=-|$)")
_re_idc_3 = re.compile(r"(^|-)u2ff[23](?=-|$)")
_re_kanji = re.compile(
    r"""-(?:
        u[23]?[\da-f]{4}(?:-u(?:e01[\da-f]{2}|fe0[\da-f]))?|
        cdp[on]?-[\da-f]{4}
    )(?=-|$)""",
    re.X)
_re_ids_kanji = re.compile(r"２-漢-漢|３-漢-漢-漢")
_re_ucs = re.compile(r"(^|-)(u[23]?[\da-f]{4})(?=-|$)")


class NamingValidator(Validator):

    name = "naming"

    def is_invalid(self, name, related, kage, gdata, dump):
        isHenka = False
        isVar = False
        if _re_var.search(name):
            name = name.rsplit("-", 2)[0]
            isVar = True
        if _re_henka.search(name):
            name = name[:-3]
            isHenka = True

        if rules["dont-create"].match(name):
            return [error_codes.PROHIBITED_GLYPH_NAME]  # 禁止されたグリフ名
        if _re_gl_glyph.match(name):
            if not _re_valid_gl.match(name[-4:]):
                # 禁止されたグリフ名（不正なGL領域の番号）
                return [error_codes.PROHIBITED_GLYPH_NAME]
        else:
            for m in _re_cdp.finditer(name):
                if not _re_valid_cdp.match(m.group(3)):
                    # 禁止されたグリフ名（不正なCDP番号）
                    return [error_codes.PROHIBITED_GLYPH_NAME]

        if _re_ids_head.match(name):
            idsReplacedName = name
            idsReplacedName = _re_idc_2.sub(r"\1２", idsReplacedName)
            idsReplacedName = _re_idc_3.sub(r"\1３", idsReplacedName)
            idsReplacedName = _re_kanji.sub("-漢", idsReplacedName)

            while _re_ids_kanji.search(idsReplacedName):
                idsReplacedName = _re_ids_kanji.sub("漢", idsReplacedName)
            if idsReplacedName != "漢":
                return [error_codes.INVALID_IDS, idsReplacedName]  # 不正なIDS

            for m in _re_cdp.finditer(name):
                cdp = m.group(1)
                cdpv = m.group(2)
                if cdpv and cdp not in cdp_dict:
                    cdp = "cdp-" + cdp[-4:]
                if cdp in cdp_dict:
                    # UCSで符号化済みのCDP外字
                    return [error_codes.ENCODED_CDP_IN_IDS, cdp, cdp_dict[cdp]]

            for m in _re_ucs.finditer(name):
                ucs = m.group(2)
                if ucs == "u3013":
                    return [error_codes.INVALID_IDS, idsReplacedName]  # 〓
                if "ue000" <= ucs <= "uf8ff":
                    return [error_codes.INVALID_IDS, idsReplacedName]  # 私用領域
            return False

        if rules["rule"].match(name):
            return False
        if not isVar and rules["rule-novar"].match(name):
            return False
        if not isHenka and rules["rule-nohenka"].match(name):
            return False
        if not isVar and not isHenka and \
                rules["rule-novar-nohenka"].match(name):
            return False

        if rules["deprecated-rule"].match(name):
            return [error_codes.DEPRECATED_NAMING_RULE]  # 廃止予定の命名規則

        return [error_codes.NAMING_RULE_VIOLATION]  # 命名規則違反


validator_class = NamingValidator
