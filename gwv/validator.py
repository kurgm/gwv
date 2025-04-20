from __future__ import annotations

import logging

from gwv import validators
from gwv.dump import Dump
from gwv.validatorctx import ValidatorContext

log = logging.getLogger(__name__)


def get_validator_name(name: str) -> str:
    return name.title() + "Validator"


def get_validator_class(name: str) -> type[validators.Validator]:
    __import__("gwv.validators." + name)
    validator_module = getattr(validators, name)
    validator_class = getattr(validator_module, get_validator_name(name))
    return validator_class


def validate(
    dump: Dump,
    validator_names: list[str] | None = None,
    *,
    ignore_error: bool = False,
):
    if validator_names is None:
        validator_names = validators.all_validator_names

    validator_instances = {
        name: get_validator_class(name)() for name in validator_names
    }

    for val in validator_instances.values():
        val.setup(dump)

    for glyphname in sorted(dump.keys()):
        entry = dump[glyphname]
        ctx = ValidatorContext(dump, entry)
        for val in validator_instances.values():
            try:
                val.validate(ctx)
            except Exception:
                log.exception(
                    "Exception while %s is validating %s",
                    type(val).__name__,
                    ctx.glyph.name,
                )
                if not ignore_error:
                    raise

    return {
        val_name: {"timestamp": dump.timestamp, "result": val.get_result()}
        for val_name, val in validator_instances.items()
    }
