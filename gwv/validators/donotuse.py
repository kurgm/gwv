from gwv.dump import Dump
from gwv.kagedata import KageData
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DO_NOT_USE="0",  # do-not-use が引用されている
)


class DonotuseValidator(Validator):

    name = "donotuse"

    filters = {
        "alias": {False},
    }

    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        quotings = []
        for line in kage.lines:
            if line.stroke_type != 99:
                continue
            part_data = dump.get(line.part_name.split("@")[0])[1]
            if part_data and "do-not-use" in part_data:
                quotings.append(line.part_name)
        if quotings:
            return [error_codes.DO_NOT_USE] + quotings
        return False
