from gwv.dump import Dump, DumpEntry
import gwv.filters as filters
from gwv.validators import Validator
from gwv.validators import ErrorCodes


error_codes = ErrorCodes(
    NOT_ALIAS="0",  # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
    NOT_ALIAS_OF_KOSEKI="1",  # koseki-xxxxx0のエイリアスでない
    NOT_ALIAS_OF_ENTITY_OF_KOSEKI="2",  # koseki-xxxxx0と異なる実体のエイリアス
)


class KosekitokiValidator(Validator):

    name = "kosekitoki"

    @filters.check_only(+filters.is_of_category({"toki"}))
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        header = entry.name[:7]
        if header != "toki-00":
            return False

        koseki_name = "koseki-" + entry.name[7:]
        if koseki_name in dump:
            koseki_entity = dump.get_entity_name(koseki_name)
        else:
            koseki_entity = koseki_name

        entity = entry.entity_name or entry.name
        if entity != koseki_entity:
            if entry.entity_name is None:
                # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
                return [error_codes.NOT_ALIAS]
            if koseki_entity == koseki_name:
                # koseki-xxxxx0のエイリアスでない
                return [error_codes.NOT_ALIAS_OF_KOSEKI, entity]
            # koseki-xxxxx0と異なる実体のエイリアス
            return [
                error_codes.NOT_ALIAS_OF_ENTITY_OF_KOSEKI,
                entity, koseki_entity]
        return False
