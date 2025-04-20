from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property

from gwv.kagedata import KageData, get_entity_name


@dataclass(frozen=True)
class DumpEntry:
    name: str
    related: str
    gdata: str

    @cached_property
    def kage(self):
        return KageData(self.gdata)

    @cached_property
    def entity_name(self):
        return get_entity_name(self.gdata)

    @cached_property
    def is_alias(self):
        return self.entity_name is not None


class Dump:
    def __init__(self, data: dict[str, tuple[str, str]], timestamp: float):
        self._data = data
        self.timestamp = timestamp

    def __getitem__(self, glyphname: str) -> DumpEntry:
        return DumpEntry(glyphname, *self._data[glyphname])

    def get(self, glyphname: str) -> DumpEntry | None:
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
        return get_entity_name(data) or glyphname

    _get_alias_of_dic: dict[str, list[str]] | None = None

    def get_alias_of(self, name: str):
        if self._get_alias_of_dic is None:
            dic = self._get_alias_of_dic = {}
            for gname in self._data:
                if gname in dic:
                    continue
                entity_name = self.get_entity_name(gname)
                if entity_name == gname:
                    continue
                dic.setdefault(entity_name, [entity_name]).append(gname)
        return self._get_alias_of_dic.get(name, [name])

    @classmethod
    def open(cls, filepath: str):
        data: dict[str, tuple[str, str]] = {}
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
