import functools
import re
from typing import Any, Callable, Container

from gwv.dump import Dump
from gwv.helper import isGokanKanji
from gwv.helper import isTogoKanji
from gwv.helper import isUcs
from gwv.kagedata import KageData


_re_ids = re.compile(r"u2ff[\dab]-")
_re_cdp = re.compile(r"cdp[on]?-[\da-f]{4}(-|$)")
_re_koseki = re.compile(r"^koseki-\d{6}$")
_re_toki = re.compile(r"^toki-\d{8}$")
_re_ext = re.compile(r"^irg201[57]-\d{5}$")
_re_bsh = re.compile(r"^unstable-bsh-[\da-f]{4}$")


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
    if _re_cdp.match(glyphname):
        return "cdp"
    if _re_koseki.match(glyphname):
        return "koseki-hikanji" if glyphname[7] == "9" else "koseki-kanji"
    if _re_toki.match(glyphname):
        return "toki"
    if _re_ext.match(glyphname):
        return "ext"
    if _re_bsh.match(glyphname):
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


class CachedPredicate:

    def __init__(self, pred: Predicate):
        self.pred = pred
        self.last_args: tuple = (None, None, None, None, None)
        self.last_result: bool = False

    def _call(self, name: str, related: str, kage: KageData, gdata: str,
              dump: Dump):
        args = (name, related, kage, gdata, dump)
        if all(arg is last_arg for arg, last_arg in zip(args, self.last_args)):
            return self.last_result

        result = self.pred(*args)
        self.last_args = args
        self.last_result = result
        return result

    def _call_inv(self, name: str, related: str, kage: KageData, gdata: str,
                  dump: Dump):
        return not self._call(name, related, kage, gdata, dump)

    def __call__(self, name: str, related: str, kage: KageData, gdata: str,
                 dump: Dump):
        return self._call(name, related, kage, gdata, dump)

    def __pos__(self):
        return self._call

    def __neg__(self):
        return self._call_inv


is_alias = CachedPredicate(
    lambda _name, _related, kage, _gdata, _dump: kage.is_alias)


has_transform = CachedPredicate(
    lambda _name, _related, kage, _gdata, _dump: kage.has_transform)


def is_of_category(categories: Container[str]):
    return CachedPredicate(
        lambda name, _related, _kage, _gdata, _dump: (
            _categorize(name) in categories))
