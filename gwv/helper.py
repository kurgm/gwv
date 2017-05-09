# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import pkg_resources
import re


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
    r"^u(4db[6-9a-f]|4d[c-f][0-9a-f]|9fe[b-f]|9ff[0-9a-f]|2a6d[7-9a-f]|2a6[ef][0-9a-f]|2b73[5-9a-f]|2b81[ef]|2cea[2-9a-f]|2ebe[1-9a-f]|2ebf[0-9a-f])$")
_re_togo_t1 = re.compile(
    r"^u(3[4-9a-f]|[4-9][0-9a-f]|2[0-9a-d][0-9a-f]|2e[0-9ab])[\da-f]{2}$")
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
    import urllib
    import urllib2
    url = "http://glyphwiki.org/wiki/Group:{}?action=edit".format(
        urllib.quote(groupname.encode("utf-8")))
    f = urllib2.urlopen(url, timeout=60)
    data = f.read()
    f.close()
    s = _re_textarea.split(data)[1]
    return [m.group(1) for m in _re_gwlink.finditer(s)]


class GWGroupLazyLoader(object):

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
    filename = pkg_resources.resource_filename("gwv", name)
    with open(filename) as f:
        dat = json.load(f)
    return dat
