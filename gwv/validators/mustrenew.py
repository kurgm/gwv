from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from gwv import filters
from gwv.validators import SingleErrorValidator, ValidatorErrorEnum, error_code

if TYPE_CHECKING:
    from gwv.validatorctx import ValidatorContext


class MustrenewValidatorError(ValidatorErrorEnum):
    @error_code("0")
    class MUSTRENEW_NO_OLD(NamedTuple):
        """最新版が旧部品を引用していない部品の旧版を引用している"""

    @error_code("@")
    class MUSTRENEW_OLD(NamedTuple):
        """最新版が旧部品を引用している部品の旧版を引用している"""


E = MustrenewValidatorError


class QuoterInfo(NamedTuple):
    is_old: bool
    quoters: set[str]


class MustrenewValidator(SingleErrorValidator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mustrenew_quoters: dict[str, QuoterInfo] = {}

    @filters.check_only(-filters.is_alias)
    @filters.check_only(-filters.is_of_category({"user-owned"}))
    def is_invalid(self, ctx: ValidatorContext):
        for line in ctx.glyph.kage.lines:
            if line.stroke_type != 99 or "@" not in line.part_name:
                continue
            part_name = line.part_name
            if part_name not in self.mustrenew_quoters:
                quoted = line.part_name.split("@", 1)[0]
                is_old = quoted in ctx.dump and "@" in ctx.dump[quoted].gdata
                self.mustrenew_quoters[part_name] = QuoterInfo(is_old, set())
            self.mustrenew_quoters[part_name].quoters.add(ctx.glyph.name)
        return False

    def get_result(self):
        no_old: list[list[str]] = []
        old: list[list[str]] = []
        for part_name in sorted(self.mustrenew_quoters.keys()):
            is_old, quoters = self.mustrenew_quoters[part_name]
            if is_old:
                old.append([part_name] + sorted(quoters))
            else:
                no_old.append([part_name] + sorted(quoters))
        return {
            E.MUSTRENEW_NO_OLD.errcode: no_old,
            E.MUSTRENEW_OLD.errcode: old,
        }
