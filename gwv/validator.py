# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools

from gwv.kagedata import KageData
from gwv import validators


def validate(dump, validator_names=None, timestamp=None):
    if validator_names is None:
        validator_names = validators.all_validator_names
    for name in validator_names:
        __import__("gwv.validators." + name)
    validator_modules = [getattr(validators, name) for name in validator_names]
    validator_instances = [mod.Validator() for mod in validator_modules]

    filternames = validators.filters.keys()

    filtered_validators = {
        k: [] for k in itertools.product(*[validators.filters[filtername] for filtername in filternames])
    }
    for mod, val in zip(validator_modules, validator_instances):
        for k in itertools.product(*[mod.filters[filtername] for filtername in filternames]):
            filtered_validators[k].append(val)

    filter_funcs = [validators.filter_funcs[filtername]
                    for filtername in filternames]

    for glyphname in sorted(dump.keys()):
        related, data = dump[glyphname]
        kage = KageData(data)
        vals = filtered_validators[
            tuple(f(glyphname, related, kage, data, dump) for f in filter_funcs)]
        for val in vals:
            val.validate(glyphname, related, kage, data)

    return {val.name: {
        "timestamp": timestamp,
        "result": val.get_result()
    } for val in validator_instances}
