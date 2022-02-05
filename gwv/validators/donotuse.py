from gwv.dump import Dump, DumpEntry
import gwv.filters as filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DO_NOT_USE="0",  # do-not-use が引用されている
)


class DonotuseValidator(Validator):

    name = "donotuse"

    @filters.check_only(-filters.is_alias)
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        quotings = []
        for line in entry.kage.lines:
            if line.stroke_type != 99:
                continue
            part_data = dump.get(line.part_name.split("@")[0])[1]
            if part_data and "do-not-use" in part_data:
                quotings.append(line.part_name)
        if quotings:
            return [error_codes.DO_NOT_USE] + quotings
        return False
