from typing import List, Optional, Type

from gwv.dump import Dump
from gwv import validators
from gwv.validatorctx import ValidatorContext


def get_validator_name(name: str) -> str:
    return name.title() + "Validator"


def get_validator_class(name: str) -> Type[validators.Validator]:
    __import__("gwv.validators." + name)
    validator_module = getattr(validators, name)
    validator_class = getattr(validator_module, get_validator_name(name))
    return validator_class


def validate(
        dump: Dump, validator_names: Optional[List[str]] = None,
        *, ignore_error: bool = False):
    if validator_names is None:
        validator_names = validators.all_validator_names

    validator_instances = {
        name: get_validator_class(name)()
        for name in validator_names
    }

    for val in validator_instances.values():
        val.ignore_error = ignore_error
        val.setup(dump)

    for glyphname in sorted(dump.keys()):
        entry = dump[glyphname]
        ctx = ValidatorContext(dump, entry)
        for val in validator_instances.values():
            val.validate(ctx)

    return {
        val_name: {
            "timestamp": dump.timestamp,
            "result": val.get_result()
        }
        for val_name, val in validator_instances.items()
    }
