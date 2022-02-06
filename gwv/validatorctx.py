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
    is_kanji: bool = field(init=False)

    def __post_init__(self):
        category = categorize(self.glyph.name)
        object.__setattr__(self, "category", category)

        is_kanji = category not in (
            "ucs-hikanji", "ucs-hikanji-var", "koseki-hikanji")
        object.__setattr__(self, "is_kanji", is_kanji)

    @cached_property
    def entity(self) -> DumpEntry:
        entity_name = self.glyph.entity_name
        if entity_name is None or entity_name not in self.dump:
            return self.glyph
        return self.dump[entity_name]
