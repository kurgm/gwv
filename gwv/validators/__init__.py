import abc
import logging

from gwv.dump import Dump, DumpEntry

logging.basicConfig()
log = logging.getLogger(__name__)

all_validator_names = [
    "corner",
    "related",
    "illegal",
    "skew",
    "donotuse",
    "kosekitoki",
    "mj",
    "ucsalias",
    "dup",
    "naming",
    "ids",
    "order",
    "delquote",
    "delvar",
    "numexp",
    "mustrenew",
    "j",
    "width",
]


class Validator(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    def __init__(self):
        self.results = {}

    def setup(self, dump: Dump):
        pass

    @abc.abstractmethod
    def is_invalid(self, entry: DumpEntry, dump: Dump):
        raise NotImplementedError

    def validate(self, entry: DumpEntry, dump: Dump):
        try:
            is_invalid = self.is_invalid(entry, dump)
        except Exception:
            log.exception(
                "Exception while %s is validating %s",
                self.name, entry.name)
            return

        if is_invalid:
            self.record(entry.name, is_invalid)

    def record(self, glyphname: str, error):
        key = str(error[0])
        if key not in self.results:
            self.results[key] = []
        self.results[key].append([glyphname] + error[1:])

    def get_result(self):
        return self.results


class ErrorCodes:

    def __init__(self, **namemap: str):
        self._map = namemap
        self._invmap = {v: k for k, v in namemap.items()}
        assert len(self._map) == len(self._invmap)

    def __getattr__(self, name: str):
        return self._map[name]

    def __getitem__(self, key: str):
        return self._invmap[key]
