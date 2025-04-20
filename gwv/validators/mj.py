from __future__ import annotations

import re
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

import gwv.filters as filters
from gwv.helper import isTogoKanji, load_package_data
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class MjValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class WRONG_ENTITY(NamedTuple):
        """entity_name のエイリアスになっているが entity_expected のエイリアスの間違い"""

        entity: str
        entity_expected: List[str]

    @error_code("1")
    class WRONG_RELATED(NamedTuple):
        """関連字に related が設定されているが ucs_expected の間違い"""

        related: str
        related_expected: List[str]

    @error_code("2")
    class RELATED_UNSET(NamedTuple):
        """関連字未設定であるが ucs_expected である"""

        related: None
        related_expected: List[str]

    @error_code("3")
    class UNDEFINED_MJ(NamedTuple):
        """欠番のMJ"""


E = MjValidatorError


def kuten2gl(ku: int, ten: int):
    """句点コードをGL領域の番号に変換する"""
    return "{:02x}{:02x}".format(ku + 32, ten + 32)


def gl2kuten(gl_: str):
    """GL領域の番号を句点コードに変換する"""
    gl = int(gl_, 16)
    return (gl >> 8) - 32, (gl & 0xFF) - 32


_re_ivs = re.compile(r"u[0-9a-f]{4,6}-ue01[0-9a-f]{2}")
_re_svs = re.compile(r"u[0-9a-f]{4,6}-ufe0[0-9a-f]")
_re_ucs = re.compile(r"u([0-9a-f]{4,6})(?:-.+)?")
_re_ids = re.compile(r"(?:u2ff[\da-f]|u31ef)-.+")
_re_koseki = re.compile(r"koseki-(\d{6})")
_re_jmj = re.compile(r"jmj-(\d{6})")
_re_juki = re.compile(r"juki-([0-9a-f]{4})")
_re_nyukan = re.compile(r"nyukan-([0-9a-f]{4})")
_re_toki = re.compile(r"toki-(\d{8})")
_re_dkw = re.compile(r"dkw-(\d{5}d{0,2}|h\d{4})")
_re_jx1 = re.compile(r"jx1-200[04]-([0-9a-f]{4})")
_re_jx2 = re.compile(r"jx2-([0-9a-f]{4})")
_re_jsp = re.compile(r"jsp-([0-9a-f]{4})")
_re_shincho = re.compile(r"shincho-(\d{5})")
_re_sdjt = re.compile(r"sdjt-(\d{5})")


class MJTable:
    FIELD_JMJ = 0
    FIELD_KOSEKI = 1
    FIELD_JUKI = 2
    FIELD_NYUKAN = 3
    FIELD_X0213 = 4
    FIELD_X0212 = 5
    FIELD_UCS = 6
    FIELD_IVS = 7
    FIELD_SVS = 8
    FIELD_TOKI = 9
    FIELD_DKW = 10
    FIELD_SHINCHO = 11
    FIELD_SDJT = 12

    n_fields = 13

    def key2gw(self, field: int, key: str):
        if field == MJTable.FIELD_UCS:
            return "u" + key
        if field in (MJTable.FIELD_IVS, MJTable.FIELD_SVS):
            return key
        if field == MJTable.FIELD_KOSEKI:
            return "koseki-" + key
        if field == MJTable.FIELD_JMJ:
            return "jmj-" + key
        if field == MJTable.FIELD_JUKI:
            return "juki-" + key
        if field == MJTable.FIELD_NYUKAN:
            return "nyukan-" + key
        if field == MJTable.FIELD_X0213:
            if key[0] == "1":
                return "jx1-2004-" + key[2:]
            return "jx2-" + key[2:]
        if field == MJTable.FIELD_X0212:
            return "jsp-" + key
        if field == MJTable.FIELD_TOKI:
            return "toki-" + key
        if field == MJTable.FIELD_DKW:
            return "dkw-" + key
        if field == MJTable.FIELD_SHINCHO:
            return "shincho-" + key
        if field == MJTable.FIELD_SDJT:
            return "sdjt-" + key

        raise KeyError(field)

    def glyphname_to_field_key(
        self, glyphname: str
    ) -> Union[Tuple[int, str], Tuple[None, None]]:
        if _re_ivs.fullmatch(glyphname):
            return MJTable.FIELD_IVS, glyphname

        if _re_svs.fullmatch(glyphname):
            return MJTable.FIELD_SVS, glyphname

        m = _re_ucs.fullmatch(glyphname)
        if m and not _re_ids.fullmatch(glyphname):
            # ucs but not ids
            return MJTable.FIELD_UCS, m.group(1)

        m = _re_koseki.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_KOSEKI, m.group(1)

        m = _re_jmj.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_JMJ, m.group(1)

        m = _re_juki.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_JUKI, m.group(1)

        m = _re_nyukan.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_NYUKAN, m.group(1)

        m = _re_toki.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_TOKI, m.group(1)

        m = _re_dkw.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_DKW, m.group(1)

        # x0213(plane 1)
        m = _re_jx1.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_X0213, "1-" + m.group(1)

        # x0213(plane 2)
        m = _re_jx2.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_X0213, "2-" + m.group(1)

        m = _re_jsp.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_X0212, m.group(1)

        m = _re_shincho.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_SHINCHO, m.group(1)

        m = _re_sdjt.fullmatch(glyphname)
        if m:
            return MJTable.FIELD_SDJT, m.group(1)

        return None, None

    def get(self, idx: int, field: int) -> List[str]:
        keys = self._table[idx][field]
        if keys is None:
            return []
        if not isinstance(keys, list):
            keys = [keys]
        return [self.key2gw(field, key) for key in keys]

    def search(self, field: int, key: str) -> List[int]:
        return self._key2indices[field].get(key.lower(), [])

    def __init__(self):
        self._table: List[List[Optional[Union[str, List[str]]]]] = load_package_data(
            "data/3rd/mj.json"
        )

        self._key2indices: List[Dict[str, List[int]]] = [
            {} for _ in range(MJTable.n_fields)
        ]
        for mjIdx, row in enumerate(self._table):
            for column, keys in enumerate(row):
                if keys is None:
                    continue
                if not isinstance(keys, list):
                    keys = [keys]
                for key in keys:
                    self._key2indices[column].setdefault(key.lower(), []).append(mjIdx)


mjtable = MJTable()


def get_base(name: str, field: int):
    if field == MJTable.FIELD_UCS:
        return name.split("-")[0]
    return name


_re_itaiji = re.compile(r"-itaiji-\d{3}$")


class MjValidator(Validator):
    @filters.check_only(
        -filters.is_of_category({"user-owned", "ids", "cdp", "ext", "bsh"})
    )
    def is_invalid(self, ctx: ValidatorContext):
        field, key = mjtable.glyphname_to_field_key(ctx.glyph.name)
        if field is None:
            return False
        assert key is not None

        indices = mjtable.search(field, key)
        if not indices:
            if field == MJTable.FIELD_JMJ and key < "090000":  # 変体仮名でない
                return E.UNDEFINED_MJ()  # 欠番のMJ
            return False

        if ctx.glyph.entity_name is not None and not _re_itaiji.search(ctx.glyph.name):
            e_field, e_key = mjtable.glyphname_to_field_key(ctx.glyph.entity_name)
            if e_field is not None and e_field != field:
                assert e_key is not None
                entity_expected = set()
                for idx in indices:
                    entity_expected.update(mjtable.get(idx, e_field))

                entity_base = get_base(ctx.glyph.entity_name, e_field)

                if entity_expected and entity_base not in entity_expected:
                    e_indices = mjtable.search(e_field, e_key)
                    expected_from_entity = set()
                    for e_idx in e_indices:
                        expected_from_entity.update(mjtable.get(e_idx, field))

                    base = get_base(ctx.glyph.name, field)

                    if expected_from_entity and base not in expected_from_entity:
                        # entity_name のエイリアスになっているが entity_expected のエイリアスの間違い
                        return E.WRONG_ENTITY(
                            ctx.glyph.entity_name, list(entity_expected)
                        )

        ucs_expected = set()
        for idx in indices:
            for ucs in mjtable.get(idx, MJTable.FIELD_UCS):
                if not isTogoKanji(ucs):
                    # グリフウィキの互換漢字には適切な関連字が設定されていると仮定する
                    ucs = ctx.dump[ucs].related if ucs in ctx.dump else "u3013"
                if ucs != "u3013":
                    ucs_expected.add(ucs)

        if ucs_expected:
            related = ctx.glyph.related
            if related == "u3013" and ctx.glyph.is_alias:
                related = ctx.entity.related
            if related == "u3013":
                # 関連字未設定であるが ucs_expected である
                return E.RELATED_UNSET(None, list(ucs_expected))
            if related not in ucs_expected:
                # 関連字に related が設定されているが ucs_expected の間違い
                return E.WRONG_RELATED(related, list(ucs_expected))
        return False
