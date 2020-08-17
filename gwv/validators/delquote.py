from gwv.validators import filters as default_filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    PART_NOT_FOUND="0",  # 無い部品を引用している
)


filters = {
    "alias": {True, False},
    "category": default_filters["category"]
}


class DelquoteValidator(Validator):

    name = "delquote"

    def is_invalid(self, name, related, kage, gdata, dump):
        for line in kage.lines:
            if line.data[0] == 99 and line.data[7].split("@")[0] not in dump:
                # 無い部品を引用している
                return [error_codes.PART_NOT_FOUND, line.data[7]]


validator_class = DelquoteValidator
