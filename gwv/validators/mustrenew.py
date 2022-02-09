from typing import List, NamedTuple, Set

import gwv.filters as filters
from gwv.validatorctx import ValidatorContext
from gwv.validators import Validator, ValidatorErrorEnum, error_code


class MustrenewValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class MUSTRENEW_NO_OLD(NamedTuple):
        """最新版が旧部品を引用していない部品の旧版を引用している"""
    @error_code("@")
    class MUSTRENEW_OLD(NamedTuple):
        """最新版が旧部品を引用している部品の旧版を引用している"""


E = MustrenewValidatorError


class MustrenewValidator(Validator):

    def __init__(self, *args, **kwargs):
        super(MustrenewValidator, self).__init__(*args, **kwargs)
        self.results[E.MUSTRENEW_NO_OLD.errcode] = {}
        self.results[E.MUSTRENEW_OLD.errcode] = {}

    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, ctx: ValidatorContext):
        quotings: Set[str] = set()
        quotings_old: Set[str] = set()  # 最新版が旧部品を引用している部品の旧版
        for line in ctx.glyph.kage.lines:
            if line.stroke_type == 99 and "@" in line.part_name:
                quoted: str = line.part_name.split("@")[0]
                if quoted in ctx.dump and "@" in ctx.dump[quoted].gdata:
                    quotings_old.add(line.part_name)
                else:
                    quotings.add(line.part_name)
        return [quotings, quotings_old] if quotings or quotings_old else False

    def record(self, glyphname: str, error: List[Set[str]]):
        quotings, quotings_old = error
        for buhinname in quotings:
            self.results[E.MUSTRENEW_NO_OLD.errcode].setdefault(
                buhinname, []).append(glyphname)
        for buhinname in quotings_old:
            self.results[E.MUSTRENEW_OLD.errcode].setdefault(
                buhinname, []).append(glyphname)

    def get_result(self):
        return {
            key: [[quoted] + val[quoted] for quoted in sorted(val.keys())]
            for key, val in self.results.items()
        }
