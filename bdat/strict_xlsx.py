from __future__ import annotations

import functools
import re
import zipfile
from typing import IO, TYPE_CHECKING, Any, Callable
from xml.etree.ElementTree import Element, iterparse

if TYPE_CHECKING:
    from collections.abc import Iterator

OOXML_NS = "{http://purl.oclc.org/ooxml/spreadsheetml/main}"


def _iterchildren(
    xmlf: IO[bytes], pred: Callable[[Element], bool]
) -> Iterator[Element]:
    it = iterparse(xmlf, ("start", "end"))
    elem: Element
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


def _tag_is(tagname: str) -> Callable[[Element], bool]:
    return lambda elem: elem.tag == tagname


def _get_strings(sstf: IO[bytes]) -> list[str]:
    def _get_string_from_sst(elem: Element) -> str:
        text = elem.findtext(OOXML_NS + "t")
        assert text is not None, "string element without text"
        return text

    return [
        _get_string_from_sst(elem)
        for elem in _iterchildren(sstf, _tag_is(OOXML_NS + "sst"))
    ]


@functools.cache
def column_to_int(column: str) -> int:
    result = 0
    for c in column:
        result *= 26
        assert "A" <= c <= "Z"
        result += ord(c) - ord("A") + 1
    return result


RE_COORD = re.compile(r"^([A-Z]{1,3})(\d+)$")


def _parse_coordinate(coord: str) -> tuple[int, int]:
    m = RE_COORD.match(coord)
    if not m:
        raise ValueError(f"invalid coordinate {coord!r}")
    column, row = m.groups()
    return column_to_int(column), int(row)


def parse_numeric(s: str) -> int | float:
    try:
        return int(s)
    except ValueError:
        return float(s)


def _itersheet(sheet: IO[bytes], strs: list[str]) -> Iterator[dict[int, Any]]:
    for rowelem in _iterchildren(sheet, _tag_is(OOXML_NS + "sheetData")):
        row: dict[int, Any] = {}
        for cellelem in rowelem:
            columnnum, _rownum = _parse_coordinate(cellelem.attrib["r"])
            vtype = cellelem.get("t", "n")

            velem = cellelem.find(OOXML_NS + "v")
            if velem is None:
                continue
            value: Any = velem.text
            if vtype == "n":
                value = parse_numeric(value)
            elif vtype == "s":
                value = strs[int(value)]
            elif vtype == "str":
                pass
            else:
                raise ValueError(f"unsupported type: {vtype!r}")
            row[columnnum] = value
        yield row


def iterxlsx(xlsx: str | IO[bytes], sheetname: str):
    archive = zipfile.ZipFile(xlsx)

    sstf = archive.open("xl/sharedStrings.xml")
    strs = _get_strings(sstf)

    sheet = archive.open(f"xl/worksheets/{sheetname}.xml")
    return _itersheet(sheet, strs)
