from typing import List, Optional, Type

from gwv.dump import Dump, DumpEntry
from gwv import validators


def get_validator_name(name: str) -> str:
    return name.title() + "Validator"


def get_validator_class(name: str) -> Type[validators.Validator]:
    __import__("gwv.validators." + name)
    validator_module = getattr(validators, name)
    validator_class = getattr(validator_module, get_validator_name(name))
    return validator_class


def validate(dump: Dump, validator_names: Optional[List[str]] = None):
    if validator_names is None:
        validator_names = validators.all_validator_names

    validator_instances = [
        get_validator_class(name)() for name in validator_names]

    for val in validator_instances:
        val.setup(dump)

    for glyphname in sorted(dump.keys()):
        related, data = dump[glyphname]
        entry = DumpEntry(glyphname, related, data)
        for val in validator_instances:
            val.validate(entry, dump)

    return {val.name: {
        "timestamp": dump.timestamp,
        "result": val.get_result()
    } for val in validator_instances}
