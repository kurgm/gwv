from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    DO_NOT_USE="0",  # do-not-use が引用されている
)


class DonotuseValidator(Validator):

    name = "donotuse"

    filters = {
        "alias": {False},
        "category": default_filters["category"]
    }

    def is_invalid(self, name, related, kage, gdata, dump):
        quotings = []
        for line in kage.lines:
            if line.data[0] != 99:
                continue
            r = dump.get(line.data[7].split("@")[0])
            if r and "do-not-use" in r[1]:
                quotings.append(line.data[7])
        if quotings:
            return [error_codes.DO_NOT_USE] + quotings
        return False


validator_class = DonotuseValidator
