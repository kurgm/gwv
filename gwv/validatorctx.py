from dataclasses import dataclass, field
from functools import cached_property

from gwv.dump import Dump, DumpEntry
from gwv.helper import categorize


@dataclass(frozen=True)
class ValidatorContext:
    """Context for per-glyph validation."""
    dump: Dump
    glyph: DumpEntry
    category: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "category", categorize(self.glyph.name))

    @cached_property
    def entity(self) -> DumpEntry:
        entity_name = self.glyph.entity_name
        if entity_name is None or entity_name not in self.dump:
            return self.glyph
        return self.dump[entity_name]
