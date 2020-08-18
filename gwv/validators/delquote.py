from gwv.dump import Dump
from gwv.kagedata import KageData
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    PART_NOT_FOUND="0",  # 無い部品を引用している
)


class DelquoteValidator(Validator):

    name = "delquote"

    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        for line in kage.lines:
            if line.data[0] == 99 and line.data[7].split("@")[0] not in dump:
                # 無い部品を引用している
                return [error_codes.PART_NOT_FOUND, line.data[7]]
        return False
