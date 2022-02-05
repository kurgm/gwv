from typing import List, Optional, Tuple


def kageInt(s: str) -> int:
    """Convert a string to an integer, in the same fashion as KAGE engine.

    It is the same as int(s) except that it returns 0 if s is an empty string.
    This behavior is an imitation of Math.floor(+s) in ECMAScript, which is
    used by KAGE engine to parse numbers in KAGE data.
    It raises a ValueError for floating-point number input or non-decimal input
    and will not try to parse (and round) it.
    """
    try:
        return int(s)
    except ValueError:
        if s.strip() == "":
            return 0
        raise


def kageIntSuppressError(s: str) -> Optional[int]:
    """The same as kageInt except that it returns None when s is invalid"""
    try:
        return kageInt(s)
    except ValueError:
        return None


class KageData:

    def __init__(self, data: str):
        self.lines = tuple([KageLine(i, l)
                            for i, l in enumerate(data.split("$"))])
        self.len = len(self.lines)
        self.is_alias = self.len == 1 and \
            self.lines[0].strdata.startswith("99:0:0:0:0:200:200:")
        self.has_transform = any(
            len(line.data) >= 2 and
            line.stroke_type == 0 and line.head_type in (97, 98, 99)
            for line in self.lines)

    def get_entity(self, dump):
        if self.is_alias:
            entity_name = self.lines[0].part_name
            if entity_name in dump:
                return dump[entity_name].kage
        return self


class KageLine:

    def __init__(self, line_number: int, data: str):
        self.line_number = line_number
        self.strdata = data
        sdata = data.split(":")
        if kageIntSuppressError(sdata[0]) == 99:
            self.data = tuple([
                kageIntSuppressError(x) if i != 7 else x
                for i, x in enumerate(sdata)])
        else:
            self.data = tuple([kageIntSuppressError(x) for x in sdata])

    @property
    def stroke_type(self) -> int:
        return self.data[0]

    @property
    def head_type(self) -> int:
        return self.data[1]

    @property
    def tail_type(self) -> int:
        return self.data[2]

    @property
    def part_name(self) -> str:
        if self.stroke_type != 99:
            raise ValueError("tried to get part name of non-part KageLine")
        return self.data[7]

    @property
    def coords(self) -> List[Tuple[int, int]]:
        if self.stroke_type == 99:
            return [(self.data[3], self.data[4]), (self.data[5], self.data[6])]

        return list(zip(self.data[3::2], self.data[4::2]))
