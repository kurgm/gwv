from __future__ import annotations

import abc
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple

from gwv.kagedata import KageLine

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gwv.dump import Dump
    from gwv.validatorctx import ValidatorContext

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


class ValidatorErrorRecorder(abc.ABC):
    @abc.abstractmethod
    def record(self, glyphname: str, error: Any) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_result(self) -> dict[str, list[Any]]:
        raise NotImplementedError()


class ValidatorErrorTupleRecorder(ValidatorErrorRecorder):
    def __init__(self):
        self._results: dict[str, list[list]] = defaultdict(list)

    def record(self, glyphname: str, error: tuple[str, Iterable]) -> None:
        key, param = error
        param = [self.param_to_serializable(p) for p in param]
        self._results[key].append([glyphname] + list(param))

    def param_to_serializable(self, p: Any) -> Any:
        if isinstance(p, KageLine):
            return (p.line_number, p.strdata)
        return p

    def get_result(self) -> dict[str, list[list]]:
        return dict(self._results)


class Validator(metaclass=abc.ABCMeta):
    recorder_cls: type[ValidatorErrorRecorder] = ValidatorErrorTupleRecorder

    def __init__(self):
        self.recorder = self.recorder_cls()

    def setup(self, dump: Dump):  # noqa: B027
        pass

    @abc.abstractmethod
    def validate(self, ctx: ValidatorContext, /) -> Any:
        pass

    def record(self, glyphname: str, error: Any):
        self.recorder.record(glyphname, error)

    def get_result(self) -> dict[str, list[Any]]:
        return self.recorder.get_result()


class SingleErrorValidator(Validator):
    @abc.abstractmethod
    def is_invalid(self, ctx: ValidatorContext, /) -> Any:
        pass

    def validate(self, ctx: ValidatorContext):
        is_invalid = self.is_invalid(ctx)

        if is_invalid:
            self.record(ctx.glyph.name, is_invalid)


class ErrorCodeAndParams(NamedTuple):
    errcode: str
    param: NamedTuple


class ValidatorErrorFactory(NamedTuple):
    errcode: str
    paramcls: type

    def __call__(self, *args, **kwargs):
        return ErrorCodeAndParams(self.errcode, self.paramcls(*args, **kwargs))


class ValidatorErrorEnum(ValidatorErrorFactory, Enum):
    """Base class for parameterized validation error.

    Usage::

        class FooValidatorError(ValidatorErrorEnum):
            @error_code("0")
            class SomeError(NamedTuple):
                some_parameter: str

        err = FooValidatorError.SomeError("a")
        assert err == ("0", ("a",))
        assert err.errcode == "0"
        assert err.param.some_parameter == "a"

        assert FooValidatorError.SomeError.errcode == "0"
        assert FooValidatorError.SomeError in FooValidatorError

        assert isinstance(err.param, FooValidatorError.SomeError.paramcls)
    """


def error_code(errcode: str):
    def decorator(func):
        return (errcode, func)

    return decorator
