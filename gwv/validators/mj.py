import re

from gwv.helper import isTogoKanji
from gwv.helper import load_package_data
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    WRONG_ENTITY="0",  # entity_name のエイリアスになっているが entity_expected のエイリアスの間違い
    WRONG_RELATED="1",  # 関連字に related が設定されているが ucs_expected の間違い
    RELATED_UNSET="2",  # 関連字未設定であるが ucs_expected である
    UNDEFINED_MJ="3",  # 欠番のMJ
)


def kuten2gl(ku, ten):
    """句点コードをGL領域の番号に変換する"""
    return "{:02x}{:02x}".format(ku + 32, ten + 32)


def gl2kuten(gl):
    """GL領域の番号を句点コードに変換する"""
    gl = int(gl, 16)
    return (gl >> 8) - 32, (gl & 0xFF) - 32


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

    def key2gw(self, field, key):
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

    def glyphname_to_field_key(self, glyphname):
        if re.compile(r"^u[0-9a-f]{4,6}-ue01[0-9a-f]{2}$").match(glyphname):
            return MJTable.FIELD_IVS, glyphname

        if re.compile(r"^u[0-9a-f]{4,6}-ufe0[0-9a-f]$").match(glyphname):
            return MJTable.FIELD_SVS, glyphname

        m = re.compile(r"^u([0-9a-f]{4,6})(-|$)").match(glyphname)
        if m and not re.compile(r"^u2ff[\dab]-").match(glyphname):
            # ucs but not ids
            return MJTable.FIELD_UCS, m.group(1)

        m = re.compile(r"^koseki-(\d{6})$").match(glyphname)
        if m:
            return MJTable.FIELD_KOSEKI, m.group(1)

        m = re.compile(r"^jmj-(\d{6})$").match(glyphname)
        if m:
            return MJTable.FIELD_JMJ, m.group(1)

        m = re.compile(r"^juki-([0-9a-f]{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_JUKI, m.group(1)

        m = re.compile(r"^nyukan-([0-9a-f]{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_NYUKAN, m.group(1)

        m = re.compile(r"^toki-(\d{8})$").match(glyphname)
        if m:
            return MJTable.FIELD_TOKI, m.group(1)

        m = re.compile(r"^dkw-(\d{5}d{0,2}|h\d{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_DKW, m.group(1)

        # x0213(plane 1)
        m = re.compile(r"^jx1-200[04]-([0-9a-f]{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_X0213, "1-" + m.group(1)

        # x0213(plane 2)
        m = re.compile(r"^jx2-([0-9a-f]{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_X0213, "2-" + m.group(1)

        m = re.compile(r"^jsp-([0-9a-f]{4})$").match(glyphname)
        if m:
            return MJTable.FIELD_X0212, m.group(1)

        m = re.compile(r"^shincho-(\d{5})$").match(glyphname)
        if m:
            return MJTable.FIELD_SHINCHO, m.group(1)

        m = re.compile(r"^sdjt-(\d{5})$").match(glyphname)
        if m:
            return MJTable.FIELD_SDJT, m.group(1)

        return None, None

    def get(self, idx, field):
        keys = self._table[idx][field]
        if keys is None:
            return []
        if not isinstance(keys, list):
            keys = [keys]
        return [self.key2gw(field, key) for key in keys]

    def search(self, field, key):
        return self._key2indices[field].get(key.lower(), [])

    def __init__(self):
        self._table = load_package_data("data/3rd/mj.json")

        self._key2indices = [{} for _ in range(MJTable.n_fields)]
        for mjIdx, row in enumerate(self._table):
            for column, keys in enumerate(row):
                if keys is None:
                    continue
                if not isinstance(keys, list):
                    keys = [keys]
                for key in keys:
                    self._key2indices[column].setdefault(
                        key.lower(), []).append(mjIdx)


mjtable = MJTable()


def get_base(name, field):
    if field == MJTable.FIELD_UCS:
        return name.split("-")[0]
    return name


class MjValidator(Validator):

    name = "mj"

    filters = {
        "category": {
            "togo", "togo-var", "gokan", "gokan-var", "ucs-hikanji",
            "ucs-hikanji-var", "koseki-kanji", "koseki-hikanji", "toki",
            "other"}
    }

    def is_invalid(self, name, related, kage, gdata, dump):
        field, key = mjtable.glyphname_to_field_key(name)
        if field is None:
            return False

        indices = mjtable.search(field, key)
        if not indices:
            if field == MJTable.FIELD_JMJ and key < "090000":  # 変体仮名でない
                return [error_codes.UNDEFINED_MJ]  # 欠番のMJ
            return False

        if kage.is_alias and not re.compile(r"-itaiji-\d{3}$").search(name):
            entity_name = gdata[19:]
            e_field, e_key = mjtable.glyphname_to_field_key(entity_name)
            if e_field is not None and e_field != field:
                entity_expected = set()
                for idx in indices:
                    entity_expected.update(mjtable.get(idx, e_field))

                entity_base = get_base(entity_name, e_field)

                if entity_expected and entity_base not in entity_expected:
                    e_indices = mjtable.search(e_field, e_key)
                    expected_from_entity = set()
                    for e_idx in e_indices:
                        expected_from_entity.update(mjtable.get(e_idx, field))

                    base = get_base(name, field)

                    if expected_from_entity and \
                            base not in expected_from_entity:
                        # entity_name のエイリアスになっているが entity_expected のエイリアスの間違い
                        return [
                            error_codes.WRONG_ENTITY,
                            entity_name, list(entity_expected)]

        ucs_expected = set()
        for idx in indices:
            for ucs in mjtable.get(idx, MJTable.FIELD_UCS):
                if not isTogoKanji(ucs):
                    # グリフウィキの互換漢字には適切な関連字が設定されていると仮定する
                    ucs = dump.get(ucs)[0] or "u3013"
                if ucs != "u3013":
                    ucs_expected.add(ucs)

        if ucs_expected:
            if related == "u3013" and kage.is_alias:
                related = dump.get(gdata[19:])[0] or "u3013"
            if related == "u3013":
                # 関連字未設定であるが ucs_expected である
                return [error_codes.RELATED_UNSET, None, list(ucs_expected)]
            if related not in ucs_expected:
                # 関連字に related が設定されているが ucs_expected の間違い
                return [error_codes.WRONG_RELATED, related, list(ucs_expected)]
        return False
