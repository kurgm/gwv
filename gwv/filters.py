import functools
import re
from typing import Any, Callable, Container, TypeVar

from gwv.dump import Dump
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.helper import isUcs
from gwv.kagedata import KageData


T = TypeVar("T")


def cache_prev(func: Callable[..., T]) -> Callable[..., T]:
    prev_args = None
    prev_result = None

    @functools.wraps(func)
    def wrapper(*args):
        nonlocal prev_args, prev_result
        if prev_args == args:
            return prev_result

        result = func(*args)
        prev_args = args
        prev_result = result
        return result

    return wrapper


_re_ids = re.compile(r"u2ff[\dab]-")
_re_cdp = re.compile(r"cdp[on]?-[\da-f]{4}(-.+)?")
_re_koseki = re.compile(r"koseki-\d{6}")
_re_toki = re.compile(r"toki-\d{8}")
_re_ext = re.compile(r"irg20(15|17|21)-\d{5}")
_re_bsh = re.compile(r"unstable-bsh-[\da-f]{4}")


@cache_prev
def _categorize(glyphname: str):
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


Predicate = Callable[[str, str, KageData, str, Dump], bool]


def check_only(pred: Predicate):

    def decorator(f: Callable[[Any, str, str, KageData, str, Dump], Any]):

        @functools.wraps(f)
        def wrapper(self: Any, name: str, related: str, kage: KageData,
                    gdata: str, dump: Dump):
            if not pred(name, related, kage, gdata, dump):
                return False
            return f(self, name, related, kage, gdata, dump)

        return wrapper

    return decorator


class BoolFunc:

    def __init__(self, func: Callable[..., bool]):
        self._func = func
        self._func_inv = lambda *args: not func(*args)

    def __call__(self, *args):
        return self._func(*args)

    def __pos__(self):
        return self._func

    def __neg__(self):
        return self._func_inv


is_alias = BoolFunc(lambda _name, _related, kage, _gdata, _dump: kage.is_alias)


has_transform = BoolFunc(lambda _name, _related, kage, _gdata, _dump:
                         kage.has_transform)


def is_of_category(categories: Container[str]):
    return BoolFunc(lambda name, _related, _kage, _gdata, _dump:
                    _categorize(name) in categories)
