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
        quotings = set()
        quotings_old = set()  # 最新版が旧部品を引用している部品の旧版
        for line in kage.lines:
            if line.data[0] == 99 and "@" in line.data[7]:
                quoted: str = line.data[7].split("@")[0]
                if quoted in dump and "@" in dump[quoted][1]:
                    quotings_old.add(line.data[7])
                else:
                    quotings.add(line.data[7])
        return [quotings, quotings_old] if quotings or quotings_old else False

    def record(self, glyphname, error):
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
