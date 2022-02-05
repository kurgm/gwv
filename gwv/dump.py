import os
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List, Optional, Tuple

from gwv.kagedata import KageData


_alias_prefix = "99:0:0:0:0:200:200:"
_alias_prefix_len = len(_alias_prefix)


class Dump:

    def __init__(self, data: Dict[str, Tuple[str, str]], timestamp: float):
        self._data = data
        self.timestamp = timestamp

    def __getitem__(self, glyphname: str):
        return DumpEntry(glyphname, *self._data[glyphname])

    def get(self, glyphname: str):
        value = self._data.get(glyphname)
        if value is None:
            return None
        return DumpEntry(glyphname, *value)

    def __contains__(self, glyphname: str):
        return glyphname in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def get_entity_name(self, glyphname: str) -> str:
        _rel, data = self._data[glyphname]
        if "$" not in data and data.startswith(_alias_prefix):
            entity = data[_alias_prefix_len:]
            if ":" not in entity:  # this should be always true
                return entity
        return glyphname

    _get_alias_of_dic: Optional[Dict[str, List[str]]] = None

    def get_alias_of(self, name: str):
        if self._get_alias_of_dic is None:
            dic = self._get_alias_of_dic = {}
            for gname in self:
                if gname in dic:
                    continue
                entity_name = self.get_entity_name(gname)
                if entity_name == gname:
                    continue
                dic.setdefault(entity_name, [entity_name]).append(gname)
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


@dataclass(frozen=True)
class DumpEntry:
    name: str
    related: str
    gdata: str

    @cached_property
    def kage(self):
        return KageData(self.gdata)
