import functools
import re
from typing import Any, Callable, Dict, IO, Iterator, List, Tuple, TypeVar, \
    Union
from xml.etree.ElementTree import Element, iterparse
import zipfile

OOXML_NS = "{http://purl.oclc.org/ooxml/spreadsheetml/main}"


def _iterchildren(xmlf: IO[bytes], pred: Callable[[Element], bool]) -> \
        Iterator[Element]:
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


def _get_strings(sstf: IO[bytes]) -> List[str]:
    return [
        elem.find(OOXML_NS + "t").text
        for elem in _iterchildren(sstf, _tag_is(OOXML_NS + "sst"))
    ]


T = TypeVar("T")


def _memoize(f: Callable[..., T]) -> Callable[..., T]:
    memo: Dict[Tuple, T] = {}

    @functools.wraps(f)
    def wrapper(*args):
        key = tuple(args)
        if key not in memo:
            memo[key] = f(*args)
        return memo[key]
    return wrapper


@_memoize
def column_to_int(column: str) -> int:
    result = 0
    for c in column:
        result *= 26
        assert "A" <= c <= "Z"
        result += ord(c) - ord("A") + 1
    return result


RE_COORD = re.compile(r"^([A-Z]{1,3})(\d+)$")


def _parse_coordinate(coord: str) -> Tuple[int, int]:
    m = RE_COORD.match(coord)
    if not m:
        raise ValueError("invalid coordinate {!r}".format(coord))
    column, row = m.groups()
    return column_to_int(column), int(row)


def parse_numeric(s: str) -> Union[int, float]:
    try:
        return int(s)
    except ValueError:
        return float(s)


def _itersheet(sheet: IO[bytes], strs: List[str]) -> Iterator[Dict[int, Any]]:
    for rowelem in _iterchildren(sheet, _tag_is(OOXML_NS + "sheetData")):
        row: Dict[int, Any] = {}
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


def iterxlsx(xlsx: Union[str, IO[bytes]], sheetname: str):
    archive = zipfile.ZipFile(xlsx)

    sstf = archive.open("xl/sharedStrings.xml")
    strs = _get_strings(sstf)

    sheet = archive.open("xl/worksheets/{}.xml".format(sheetname))
    return _itersheet(sheet, strs)
