from gwv.dump import Dump
import gwv.filters as filters
from gwv.kagedata import KageData
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
    def is_invalid(self, name: str, related: str, kage: KageData, gdata: str,
                   dump: Dump):
        header = name[:7]
        if header != "toki-00":
            return False

        koseki_name = "koseki-" + name[7:]
        if koseki_name in dump:
            koseki_entity = dump.get_entity_name(koseki_name)
        else:
            koseki_entity = koseki_name

        if not kage.is_alias:
            entity = name
            if entity != koseki_entity:
                # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
                return [error_codes.NOT_ALIAS]
        else:
            entity = kage.lines[0].part_name
            if entity != koseki_entity:
                if koseki_entity == koseki_name:
                    # koseki-xxxxx0のエイリアスでない
                    return [error_codes.NOT_ALIAS_OF_KOSEKI, entity]
                # koseki-xxxxx0と異なる実体のエイリアス
                return [
                    error_codes.NOT_ALIAS_OF_ENTITY_OF_KOSEKI,
                    entity, koseki_entity]
        return False
