from dataclasses import dataclass, field
from functools import cached_property

from gwv.dump import Dump, DumpEntry
from gwv.helper import CategoryParam, CategoryType, categorize, is_hikanji


@dataclass(frozen=True)
class ValidatorContext:
    """Context for per-glyph validation."""
    dump: Dump
    glyph: DumpEntry

    category: CategoryType = field(init=False)
    category_param: CategoryParam = field(init=False)
    is_kanji: bool = field(init=False)

    def __post_init__(self):
        category_param = categorize(self.glyph.name)
        object.__setattr__(self, "category_param", category_param)
        object.__setattr__(self, "category", category_param[0])

        is_kanji = not is_hikanji(category_param)
        object.__setattr__(self, "is_kanji", is_kanji)

    @cached_property
    def entity(self) -> DumpEntry:
        entity_name = self.glyph.entity_name
        if entity_name is None or entity_name not in self.dump:
            return self.glyph
        return self.dump[entity_name]
