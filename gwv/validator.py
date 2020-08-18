import itertools
from typing import Dict, List, Optional, Type

from gwv.dump import Dump
from gwv.kagedata import KageData
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

    filternames = validators.filters.keys()

    filtered_validators: Dict[tuple, List[validators.Validator]] = {
        k: []
        for k in itertools.product(*[
            validators.filters[filtername] for filtername in filternames])
    }
    for val in validator_instances:
        for k in itertools.product(*[
                val.filters.get(filtername, validators.filters[filtername])
                for filtername in filternames]):
            filtered_validators[k].append(val)

    filter_funcs = [validators.filter_funcs[filtername]
                    for filtername in filternames]

    for val in validator_instances:
        val.setup(dump)

    for glyphname in sorted(dump.keys()):
        related, data = dump[glyphname]
        kage = KageData(data)
        vals = filtered_validators[
            tuple(f(glyphname, related, kage, data) for f in filter_funcs)]
        for val in vals:
            val.validate(glyphname, related, kage, data, dump)

    return {val.name: {
        "timestamp": dump.timestamp,
        "result": val.get_result()
    } for val in validator_instances}
