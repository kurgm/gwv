# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import functools
import re
from xml.etree.ElementTree import iterparse
import zipfile

OOXML_NS = "{http://purl.oclc.org/ooxml/spreadsheetml/main}"


def _iterchildren(xmlf, pred):
    it = iterparse(xmlf, ("start", "end"))
    for evt, elem in it:
        if evt == "start" and pred(elem):
            break
    else:
        return

    parent = elem
    depth = 0
    for evt, elem in it:
        if evt == "start":
            depth += 1
        elif evt == "end":
            depth -= 1
            if depth == 0:
                yield elem
                parent.clear()
            if depth < 0:
                return


def _tag_is(tagname):
    return lambda elem: elem.tag == tagname


def _get_strings(sstf):
    return [
        elem.find(OOXML_NS + "t").text
        for elem in _iterchildren(sstf, _tag_is(OOXML_NS + "sst"))
    ]


def _memoize(f):
    memo = {}
    @functools.wraps(f)
    def wrapper(*args):
        key = tuple(args)
        if key not in memo:
            memo[key] = f(*args)
        return memo[key]
    return wrapper


@_memoize
def column_to_int(column):
    result = 0
    for c in column:
        result *= 26
        assert "A" <= c <= "Z"
        result += ord(c) - ord("A") + 1
    return result


RE_COORD = re.compile(r"^([A-Z]{1,3})(\d+)$")


def _parse_coordinate(coord):
    m = RE_COORD.match(coord)
    if not m:
        raise ValueError("invalid coordinate {!r}".format(coord))
    column, row = m.groups()
    return column_to_int(column), int(row)


def parse_numeric(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def _itersheet(sheet, strs):
    for rowelem in _iterchildren(sheet, _tag_is(OOXML_NS + "sheetData")):
        row = {}
        for cellelem in rowelem:
            columnnum, _rownum = _parse_coordinate(cellelem.get("r"))
            vtype = cellelem.get("t", "n")

            value = cellelem.find(OOXML_NS + "v").text
            if vtype == "n":
                value = parse_numeric(value)
            elif vtype == "s":
                value = strs[int(value)]
            elif vtype == "str":
                pass
            else:
                raise ValueError("unsupported type: {!r}".format(vtype))
            row[columnnum] = value
        yield row


def iterxlsx(xlsx, sheetname):
    archive = zipfile.ZipFile(xlsx)

    sstf = archive.open("xl/sharedStrings.xml")
    strs = _get_strings(sstf)

    sheet = archive.open("xl/worksheets/{}.xml".format(sheetname))
    return _itersheet(sheet, strs)
