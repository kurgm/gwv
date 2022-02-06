import json
import os.path
import re
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import quote
from urllib.request import urlopen

import yaml
import pkg_resources


_re_ids = re.compile(r"u2ff[\dab]-")
_re_cdp = re.compile(r"cdp[on]?-[\da-f]{4}(-.+)?")
_re_koseki = re.compile(r"koseki-\d{6}")
_re_toki = re.compile(r"toki-\d{8}")
_re_ext = re.compile(r"irg20(15|17|21)-\d{5}")
_re_bsh = re.compile(r"unstable-bsh-[\da-f]{4}")


def isKanji(name: str):
    if _re_ids.match(name):
        return True
    header = name.split("-")[0]
    if isUcs(header):
        return isTogoKanji(header) or isGokanKanji(header)
    if _re_koseki.fullmatch(name):
        return name[7] != "9"
    return True


def range_inclusive(stt: int, end: int):
    return range(stt, end + 1)


_togo_ranges = [
    range_inclusive(0x3400, 0x4dbf),    # Ext A
    range_inclusive(0x4e00, 0x9fff),    # URO
    range_inclusive(0x20000, 0x2a6df),  # Ext B
    range_inclusive(0x2a700, 0x2b738),  # Ext C
    range_inclusive(0x2b740, 0x2b81d),  # Ext D
    range_inclusive(0x2b820, 0x2cea1),  # Ext E
    range_inclusive(0x2ceb0, 0x2ebe0),  # Ext F
    range_inclusive(0x30000, 0x3134a),  # Ext G
]

_togo_in_compat = {
    0xfa0e, 0xfa0f,
    0xfa11, 0xfa13, 0xfa14, 0xfa1f,
    0xfa21, 0xfa23, 0xfa24, 0xfa27, 0xfa28, 0xfa29,
}

_gokan_ranges = [
    range_inclusive(0xf900, 0xfa6d),
    range_inclusive(0xfa70, 0xfad9),
    range_inclusive(0x2f800, 0x2fa1d),
]


def isTogoKanji(name: str):
    cp = get_ucs_codepoint(name)
    if cp is None:
        return False
    return any(cp in trange for trange in _togo_ranges) or \
        cp in _togo_in_compat


def isGokanKanji(name: str):
    cp = get_ucs_codepoint(name)
    if cp is None:
        return False
    return any(cp in grange for grange in _gokan_ranges) and \
        cp not in _togo_in_compat


_re_ucs = re.compile(r"u[\da-f]{4,6}")
RE_REGIONS = r"(?:[gtv]v?|[hmis]|k[pv]?|u[ks]?|j[asv]?)"


def isUcs(name: str):
    return _re_ucs.fullmatch(name)


def get_ucs_codepoint(name: str):
    if not isUcs(name):
        return None
    return int(name[1:], 16)


def categorize(glyphname: str):
    if "_" in glyphname:
        return "user-owned"
    splitname = glyphname.split("-")
    header = splitname[0]
    if isUcs(header):
        if _re_ids.match(glyphname):
            return "ids"
        if isTogoKanji(header):
            return "togo" if len(splitname) == 1 else "togo-var"
        if isGokanKanji(header):
            return "gokan" if len(splitname) == 1 else "gokan-var"
        return "ucs-hikanji" if len(splitname) == 1 else "ucs-hikanji-var"
    if _re_cdp.fullmatch(glyphname):
        return "cdp"
    if _re_koseki.fullmatch(glyphname):
        return "koseki-hikanji" if glyphname[7] == "9" else "koseki-kanji"
    if _re_toki.fullmatch(glyphname):
        return "toki"
    if _re_ext.fullmatch(glyphname):
        return "ext"
    if _re_bsh.fullmatch(glyphname):
        return "bsh"
    return "other"


def isYoko(x0: int, y0: int, x1: int, y1: int) -> bool:
    if y0 == y1 and x0 != x1:
        return True
    dx = x1 - x0
    dy = y1 - y0
    return -dx < dy < dx


_re_textarea = re.compile(r"</?textarea(?: [^>]*)?>")
_re_gwlink = re.compile(r"\[\[(?:[^]]+\s)?([0-9a-z_-]+(?:@\d+)?)\]\]")


def getGlyphsInGroup(groupname: str) -> List[str]:
    url = "https://glyphwiki.org/wiki/Group:{}?action=edit".format(
        quote(groupname.encode("utf-8")))
    f = urlopen(url, timeout=60)
    data = f.read().decode("utf-8")
    f.close()
    s = _re_textarea.split(data)[1]
    return [m.group(1) for m in _re_gwlink.finditer(s)]


class GWGroupLazyLoader:

    def __init__(self, groupname: str, isset: bool = False):
        self.groupname = groupname
        self.isset = isset
        self.data: Union[List[str], Set[str]]

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
    with pkg_resources.resource_stream("gwv", name) as f:
        ext = os.path.splitext(name)[1]
        if ext == ".json":
            return json.load(f)
        if ext in (".yaml", ".yml"):
            return yaml.safe_load(f)
        if ext == ".txt":
            return f.read()

        raise ValueError("Unknown data file extension: {!r}".format(ext))


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
        self.data: Dict[str, List[Optional[str]]]

    def load(self):
        self.data = load_package_data("data/3rd/cjksrc.json")

    def get(self, ucs: str, column: int) -> Optional[str]:
        if not hasattr(self, "data"):
            self.load()
        record = self.data.get(ucs)
        if record is None:
            return None
        return record[column]


cjk_sources = CJKSources()
