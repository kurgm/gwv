from dataclasses import dataclass
from functools import cached_property

from gwv.dump import Dump, DumpEntry


@dataclass(frozen=True)
class ValidatorContext:
    """Context for per-glyph validation."""
    dump: Dump
    glyph: DumpEntry

    @cached_property
    def entity(self) -> DumpEntry:
        entity_name = self.glyph.entity_name
        if entity_name is None or entity_name not in self.dump:
            return self.glyph
        return self.dump[entity_name]
