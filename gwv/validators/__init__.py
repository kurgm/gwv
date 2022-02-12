import abc
from enum import Enum
import logging
from typing import Any, Dict, Iterable, List, NamedTuple, Tuple

from gwv.dump import Dump
from gwv.validatorctx import ValidatorContext

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

    def __init__(self):
        self.results: Dict[str, Any] = {}

    def setup(self, dump: Dump):
        pass

    @abc.abstractmethod
    def is_invalid(self, ctx: ValidatorContext) -> Any:
        raise NotImplementedError

    def validate(self, ctx: ValidatorContext):
        try:
            is_invalid = self.is_invalid(ctx)
        except Exception:
            log.exception(
                "Exception while %s is validating %s",
                type(self).__name__, ctx.glyph.name)
            return

        if is_invalid:
            self.record(ctx.glyph.name, is_invalid)

    def record(self, glyphname: str, error: Tuple[str, Iterable]):
        key, param = error
        key = str(key)
        param = list(param)
        if key not in self.results:
            self.results[key] = []
        self.results[key].append([glyphname] + param)

    def get_result(self) -> Dict[str, List[Any]]:
        return self.results


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
    pass


def error_code(errcode: str):
    def decorator(func):
        return (errcode, func)
    return decorator
