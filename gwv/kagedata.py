import math


def kageInt(s):
    """Imitates Math.floor(+s) in ECMAScript (returns an int).

    KAGE Engine uses Math.floor to parse numbers in KAGE data.
    """
    s = s.strip()
    if s == "":
        return 0
    try:
        # decimal integer literal (may have leading 0 digits)
        return int(s)
    except ValueError:
        try:
            # hexadecimal, octal, binary integer literal
            return int(s, 0)
        except ValueError:
            # contains decimal point and/or exponent part
            return int(math.floor(float(s)))


def kageIntSuppressError(s):
    """The same as kageInt except that it returns None when s is invalid"""
    try:
        return kageInt(s)
    except (ValueError, OverflowError):
        return None


class KageData:

    def __init__(self, data):
        self.lines = tuple([KageLine(i, l)
                            for i, l in enumerate(data.split("$"))])
        self.len = len(self.lines)
        self.is_alias = self.len == 1 and \
            self.lines[0].strdata.startswith("99:0:0:0:0:200:200:")
        self.has_transform = any(
            len(line.data) >= 2 and
            line.data[0] == 0 and line.data[1] in (97, 98, 99)
            for line in self.lines)

    def get_entity(self, dump):
        if self.is_alias:
            entity_name = self.lines[0].data[7]
            if entity_name in dump:
                return KageData(dump[entity_name][1])
        return self


class KageLine:

    def __init__(self, line_number, data):
        self.line_number = line_number
        self.strdata = data
        sdata = data.split(":")
        if kageIntSuppressError(sdata[0]) != 99:
            self.data = tuple([kageIntSuppressError(x) for x in sdata])
        else:
            self.data = tuple([
                kageIntSuppressError(x) if i != 7 else x
                for i, x in enumerate(sdata)])
