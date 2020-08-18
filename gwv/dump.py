import os
from typing import Dict, List, Optional, Tuple

from gwv.kagedata import KageData


class Dump:

    def __init__(self, data: Dict[str, Tuple[str, str]], timestamp: float):
        self._data = data
        self.timestamp = timestamp

    def __getitem__(self, glyphname: str):
        return self._data[glyphname]

    def get(self, glyphname: str):
        return self._data.get(glyphname, (None, None))

    def __contains__(self, glyphname: str):
        return glyphname in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get_entity_name(self, glyphname: str) -> str:
        _rel, data = self[glyphname]
        if "$" not in data and data.startswith("99:0:0:0:0:200:200:"):
            return data.split(":")[7]
        return glyphname

    _get_alias_of_dic: Optional[Dict[str, List[str]]] = None

    def get_alias_of(self, name: str):
        if self._get_alias_of_dic is None:
            self._get_alias_of_dic = {}
            for gname in self:
                if gname in self._get_alias_of_dic:
                    continue
                kage = KageData(self[gname][1])
                if not kage.is_alias:
                    continue
                entity_name = self.get_entity_name(gname)
                entry = self._get_alias_of_dic.setdefault(
                    entity_name, [entity_name])
                entry.append(gname)
                self._get_alias_of_dic[gname] = entry
        return self._get_alias_of_dic.get(name, [name])

    @classmethod
    def open(cls, filepath: str):
        data: Dict[str, Tuple[str, str]] = {}
        with open(filepath) as fp:
            if filepath[-4:] == ".csv":
                # first line contains the last modified time
                timestamp = float(fp.readline()[:-1])
                for line in fp:
                    row = line.rstrip("\n").split(",")
                    if len(row) != 3:
                        continue
                    data[row[0]] = (row[1], row[2])
            else:
                # dump_newest_only.txt
                timestamp = os.path.getmtime(filepath)
                line = fp.readline()  # header
                line = fp.readline()  # ------
                for line in iter(fp.readline, ""):
                    row = [x.strip() for x in line.split("|")]
                    if len(row) != 3:
                        continue
                    data[row[0]] = (row[1], row[2])

        return cls(data, timestamp)
