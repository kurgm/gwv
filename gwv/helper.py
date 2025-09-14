from __future__ import annotations

import importlib.resources
import json
import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote
from urllib.request import urlopen

import yaml


def range_inclusive(stt: int, end: int):
    return range(stt, end + 1)


_togo_ranges = [
    range_inclusive(0x3400, 0x4DBF),  # Ext A
    range_inclusive(0x4E00, 0x9FFF),  # URO
    range_inclusive(0x20000, 0x2A6DF),  # Ext B
    range_inclusive(0x2A700, 0x2B73F),  # Ext C
    range_inclusive(0x2B740, 0x2B81D),  # Ext D
    range_inclusive(0x2B820, 0x2CEAD),  # Ext E
    range_inclusive(0x2CEB0, 0x2EBE0),  # Ext F
    range_inclusive(0x2EBF0, 0x2EE5D),  # Ext I
    range_inclusive(0x30000, 0x3134A),  # Ext G
    range_inclusive(0x31350, 0x323AF),  # Ext H
    range_inclusive(0x323B0, 0x33479),  # Ext J
]

_togo_in_compat = {
    0xFA0E,
    0xFA0F,
    0xFA11,
    0xFA13,
    0xFA14,
    0xFA1F,
    0xFA21,
    0xFA23,
    0xFA24,
    0xFA27,
    0xFA28,
    0xFA29,
}

_gokan_ranges = [
    range_inclusive(0xF900, 0xFA6D),
    range_inclusive(0xFA70, 0xFAD9),
    range_inclusive(0x2F800, 0x2FA1D),
]


def is_togo_kanji_cp(cp: int):
    return any(cp in trange for trange in _togo_ranges) or cp in _togo_in_compat


def is_gokan_kanji_cp(cp: int):
    return any(cp in grange for grange in _gokan_ranges) and cp not in _togo_in_compat


RE_REGIONS = r"(?:[gtvh]v?|[mis]|k[pv]?|u[ks]?|j[asvn]?)"

_re_ucs = re.compile(r"u([\da-f]{4,6})")


def get_ucs_codepoint(name: str):
    m = _re_ucs.fullmatch(name)
    if not m:
        return None
    return int(m.group(1), 16)


def isTogoKanji(name: str):
    cp = get_ucs_codepoint(name)
    if cp is None:
        return False
    return is_togo_kanji_cp(cp)


def isGokanKanji(name: str):
    cp = get_ucs_codepoint(name)
    if cp is None:
        return False
    return is_gokan_kanji_cp(cp)


_re_categorize = re.compile(
    r"""
    (?P<ids>    (?:u2ff[\da-f]|u31ef)-.+)|
    (?P<UCS>    u([\da-f]{4,6})((?:-.+)?))|
    (?P<cdp>    (cdp[on]?)-([\da-f]{4})(?:(-.+)?))|
    (?P<koseki> koseki-(\d{6}))|
    (?P<toki>   toki-(\d{8}))|
    (?P<ext>    irg(20(?:15|17|21))-(\d{5}))|
    (?P<bsh>    unstable-bsh-([\da-f]{4}))|
""",
    re.VERBOSE,
)

CategoryType = Literal[
    "user-owned",
    "ids",
    "ucs-kanji",
    "ucs-hikanji",
    "cdp",
    "koseki",
    "toki",
    "ext",
    "bsh",
    "other",
]
CategoryParam = tuple[CategoryType, tuple[str, ...]]


def categorize(glyphname: str) -> CategoryParam:
    if "_" in glyphname:
        return "user-owned", ()
    m = _re_categorize.fullmatch(glyphname)
    if m is None:
        return "other", ()
    category = m.lastgroup
    assert category is not None
    params = tuple(s for s in m.groups(None) if s is not None)[1:]

    if category == "UCS":
        cp = int(params[0], 16)
        if is_togo_kanji_cp(cp) or is_gokan_kanji_cp(cp):
            category = "ucs-kanji"
        else:
            category = "ucs-hikanji"

    return category, params  # type: ignore


def is_hikanji(category_param: CategoryParam) -> bool:
    category, params = category_param
    if category == "ucs-hikanji":
        return True
    if category == "koseki":
        return params[0][0] == "9"
    return False


def isYoko(x0: int, y0: int, x1: int, y1: int) -> bool:
    if y0 == y1 and x0 != x1:
        return True
    dx = x1 - x0
    dy = y1 - y0
    return -dx < dy < dx


_re_textarea = re.compile(r"</?textarea(?: [^>]*)?>")
_re_gwlink = re.compile(r"\[\[(?:[^]]+\s)?([0-9a-z_-]+(?:@\d+)?)\]\]")


def getGlyphsInGroup(groupname: str) -> list[str]:
    encoded_group_name = quote(groupname.encode("utf-8"))
    url = f"https://glyphwiki.org/wiki/Group:{encoded_group_name}?action=edit"
    f = urlopen(url, timeout=60)
    data = f.read().decode("utf-8")
    f.close()
    s = _re_textarea.split(data)[1]
    return [m.group(1) for m in _re_gwlink.finditer(s)]


class GWGroupLazyLoader:
    def __init__(self, groupname: str, isset: bool = False):
        self.groupname = groupname
        self.isset = isset
        self.data: list[str] | set[str]

    def load(self):
        glyphs = getGlyphsInGroup(self.groupname)
        if self.isset:
            self.data = set(glyphs)
        else:
            self.data = glyphs

    def get_data(self):
        if not hasattr(self, "data"):
            self.load()
        return self.data


def load_package_data(name: str) -> Any:
    with importlib.resources.files("gwv").joinpath(name).open("rb") as f:
        ext = Path(name).suffix
        if ext == ".json":
            return json.load(f)
        if ext in (".yaml", ".yml"):
            return yaml.safe_load(f)
        if ext == ".txt":
            return f.read()

        raise ValueError(f"Unknown data file extension: {ext!r}")


class CJKSources:
    COLUMN_G = 0
    COLUMN_T = 1
    COLUMN_J = 2
    COLUMN_K = 3
    COLUMN_KP = 4
    COLUMN_V = 5
    COLUMN_H = 6
    COLUMN_M = 7
    COLUMN_U = 8
    COLUMN_S = 9
    COLUMN_UK = 10
    COLUMN_COMPATIBILITY_VARIANT = 11

    region2index = {
        "g": COLUMN_G,
        "t": COLUMN_T,
        "j": COLUMN_J,
        "k": COLUMN_K,
        "kp": COLUMN_KP,
        "v": COLUMN_V,
        "h": COLUMN_H,
        "m": COLUMN_M,
        "u": COLUMN_U,
        "s": COLUMN_S,
        "uk": COLUMN_UK,
    }

    def __init__(self):
        self.data: dict[str, list[str | None]]

    def load(self):
        self.data = load_package_data("data/3rd/cjksrc.json")

    def get(self, ucs: str, column: int) -> str | None:
        if not hasattr(self, "data"):
            self.load()
        record = self.data.get(ucs)
        if record is None:
            return None
        return record[column]


cjk_sources = CJKSources()
