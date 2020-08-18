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
            if line.stroke_type == 99 and \
                    line.part_name.split("@")[0] not in dump:
                # 無い部品を引用している
                return [error_codes.PART_NOT_FOUND, line.part_name]
        return False
