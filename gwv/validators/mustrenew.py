from typing import List, Set

from gwv.dump import Dump
from gwv.kagedata import KageData
from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    MUSTRENEW_NO_OLD="0",  # 最新版が旧部品を引用していない部品の旧版を引用している
    MUSTRENEW_OLD="@",  # 最新版が旧部品を引用している部品の旧版を引用している
)


class MustrenewValidator(Validator):

    name = "mustrenew"

    filters = {
        "alias": {False},
        "category": default_filters["category"] - {"user-owned"}
    }

    def __init__(self, *args, **kwargs):
        super(MustrenewValidator, self).__init__(*args, **kwargs)
        self.results["0"] = {}
        self.results["@"] = {}

    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        quotings: Set[str] = set()
        quotings_old: Set[str] = set()  # 最新版が旧部品を引用している部品の旧版
        for line in kage.lines:
            if line.stroke_type == 99 and "@" in line.part_name:
                quoted: str = line.part_name.split("@")[0]
                if quoted in dump and "@" in dump[quoted][1]:
                    quotings_old.add(line.part_name)
                else:
                    quotings.add(line.part_name)
        return [quotings, quotings_old] if quotings or quotings_old else False

    def record(self, glyphname: str, error: List[Set[str]]):
        quotings, quotings_old = error
        for buhinname in quotings:
            self.results[error_codes.MUSTRENEW_NO_OLD].setdefault(
                buhinname, []).append(glyphname)
        for buhinname in quotings_old:
            self.results[error_codes.MUSTRENEW_OLD].setdefault(
                buhinname, []).append(glyphname)

    def get_result(self):
        return {
            key: [[quoted] + val[quoted] for quoted in sorted(val.keys())]
            for key, val in self.results.items()
        }
