import json
import os.path
import re
from urllib.parse import quote
from urllib.request import urlopen

import yaml
import pkg_resources

from gwv.kagedata import KageData


_re_ids = re.compile(r"u2ff[\dab]-")
_re_koseki = re.compile(r"^koseki-\d{6}$")


def isKanji(name):
    if _re_ids.match(name):
        return True
    header = name.split("-")[0]
    if isUcs(header):
        return isTogoKanji(header) or isGokanKanji(header)
    if _re_koseki.match(name):
        return name[7] != "9"
    return True


_re_togo_f = re.compile(
    r"""^u(
        4d[c-f][0-9a-f]|              # Ext A
        9ff[d-f]|                     # URO
        2a6d[ef]|2a6[ef][0-9a-f]|     # Ext B
        2b73[5-9a-f]|                 # Ext C
        2b81[ef]|                     # Ext D
        2cea[2-9a-f]|                 # Ext E
        2ebe[1-9a-f]|2ebf[0-9a-f]|    # Ext F
        3134[b-f]|313[5-9a-f][0-9a-f] # Ext G
    )$""",
    re.X)
_re_togo_t1 = re.compile(
    r"""^u(
        3[4-9a-f]|          # Ext A
        [4-9][0-9a-f]|      # URO
        2[0-9a-d][0-9a-f]|  # Ext B, C, D, E, F
        2e[0-9ab]|          # Ext F
        30[0-9a-f]|31[0-3]  # Ext G
    )[\da-f]{2}$""",
    re.X)
_re_togo_t2 = re.compile(r"^ufa(0[ef]|1[134f]|2[134789])$")


def isTogoKanji(name):
    if _re_togo_f.match(name):
        return False
    if _re_togo_t1.match(name):
        return True
    if _re_togo_t2.match(name):
        return True
    return False


_re_gokan_f = re.compile(r"^ufa(6[ef]|d[a-f]|[ef][\da-f])$")
_re_gokan_t1 = re.compile(r"^uf[9a][\da-f]{2}$")
_re_gokan_t2 = re.compile(r"^u2f([89][\da-f]{2}|a0[\da-f]|a1[\da-d])$")


def isGokanKanji(name):
    if _re_gokan_f.match(name):
        return False
    if _re_togo_t2.match(name):
        return False
    if _re_gokan_t1.match(name):
        return True
    if _re_gokan_t2.match(name):
        return True
    return False


_re_ucs = re.compile(r"^u[\da-f]{4,6}$")
RE_REGIONS = r"(?:[gtv]v?|[hmis]|k[pv]?|u[ks]?|j[asv]?)"


def isUcs(name):
    return _re_ucs.match(name)


def isYoko(x0, y0, x1, y1):
    if y0 == y1 and x0 != x1:
        return True
    dx = x1 - x0
    dy = y1 - y0
    return -dx < dy < dx


_re_textarea = re.compile(r"</?textarea(?: [^>]*)?>")
_re_gwlink = re.compile(r"\[\[(?:[^]]+\s)?([0-9a-z_-]+(?:@\d+)?)\]\]")


def getGlyphsInGroup(groupname):
    url = "http://glyphwiki.org/wiki/Group:{}?action=edit".format(
        quote(groupname.encode("utf-8")))
    f = urlopen(url, timeout=60)
    data = f.read().decode("utf-8")
    f.close()
    s = _re_textarea.split(data)[1]
    return [m.group(1) for m in _re_gwlink.finditer(s)]


class GWGroupLazyLoader:

    def __init__(self, groupname, isset=False):
        self.groupname = groupname
        self.isset = isset
        self.data = None

    def load(self):
        glyphs = getGlyphsInGroup(self.groupname)
        if self.isset:
            self.data = set(glyphs)
        else:
            self.data = glyphs

    def get_data(self):
        if self.data is None:
            self.load()
        return self.data


def load_package_data(name):
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
        self.data = None

    def load(self):
        self.data = load_package_data("data/3rd/cjksrc.json")

    def get(self, ucs, column):
        if self.data is None:
            self.load()
        record = self.data.get(ucs)
        if record is None:
            return None
        return record[column]


cjk_sources = CJKSources()


def get_alias_of(dump, name):
    if get_alias_of.dic is not None:
        return get_alias_of.dic.get(name, [name])
    get_alias_of.dic = {}
    for gname in dump:
        if gname in get_alias_of.dic:
            continue
        kage = KageData(dump[gname][1])
        if not kage.is_alias:
            continue
        entity_name = kage.lines[0].data[7]
        entry = get_alias_of.dic.setdefault(entity_name, [entity_name])
        entry.append(gname)
        get_alias_of.dic[gname] = entry
    return get_alias_of(dump, name)


get_alias_of.dic = None
