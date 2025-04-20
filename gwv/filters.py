from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable

from gwv.validatorctx import ValidatorContext

if TYPE_CHECKING:
    from collections.abc import Container

    from gwv.helper import CategoryType

Predicate = Callable[[ValidatorContext], bool]


def check_only(pred: Predicate):
    def decorator(f: Callable[[Any, ValidatorContext], Any]):
        @functools.wraps(f)
        def wrapper(self: Any, ctx: ValidatorContext):
            if not pred(ctx):
                return False
            return f(self, ctx)

        return wrapper

    return decorator


class BoolFunc:
    def __init__(self, func: Callable[..., bool]):
        self._func = func
        self._func_inv = lambda *args: not func(*args)

    def __call__(self, *args):
        return self._func(*args)

    def __pos__(self):
        return self._func

    def __neg__(self):
        return self._func_inv


@BoolFunc
def is_alias(ctx: ValidatorContext):
    return ctx.glyph.is_alias


@BoolFunc
def has_transform(ctx: ValidatorContext):
    return ctx.glyph.kage.has_transform


def is_of_category(categories: Container[CategoryType]):
    @BoolFunc
    def is_of_given_category(ctx: ValidatorContext):
        return ctx.category in categories

    return is_of_given_category


@BoolFunc
def is_hikanji(ctx: ValidatorContext):
    return ctx.is_hikanji
