# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re


def isAlias(data):
    return len(data) == 1 and data[0][:19] == "99:0:0:0:0:200:200:"


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


_re_togo_f = re.compile(r"^u(4db[6-9a-f]|4d[c-f][0-9a-f]|9fe[a-f]|9ff[0-9a-f]|2a6d[7-9a-f]|2a6[ef][0-9a-f]|2b73[5-9a-f]|2b81[ef]|2cea[2-9a-f]|2ce[b-f][0-9a-f])$")
_re_togo_t1 = re.compile(r"^u(3[4-9a-f]|[4-9][0-9a-f]|2[0-9ab][0-9a-f]|2c[0-9a-e])[\da-f]{2}$")
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
