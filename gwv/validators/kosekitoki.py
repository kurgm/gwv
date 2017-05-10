# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.kagedata import KageData
from gwv.validators import ValidatorClass

filters = {
    "alias": {True, False},
    "category": {"toki"}
}


class Validator(ValidatorClass):

    name = "kosekitoki"

    def is_invalid(self, name, related, kage, gdata, dump):
        header = name[:7]
        if header != "toki-00":
            return False

        koseki_name = "koseki-" + name[7:]
        koseki_entity = koseki_name

        koseki_gdata = dump.get(koseki_name, (None, None))[1]
        if koseki_gdata is not None:
            koseki_kage = KageData(koseki_gdata)
            if koseki_kage.isAlias():
                koseki_entity = koseki_kage.lines[0].data[7]

        if not kage.isAlias():
            entity = name
            if entity != koseki_entity:
                # エイリアスでない（し、koseki-xxxxx0がtoki-00xxxxx0のエイリアスというわけでもない）
                return [0]
        else:
            entity = kage.lines[0].data[7]
            if entity != koseki_entity:
                if koseki_entity == koseki_name:
                    # koseki-xxxxx0のエイリアスでない
                    return [1, entity]
                else:
                    # koseki-xxxxx0と異なる実体のエイリアス
                    return [2, entity, koseki_entity]
        return False
