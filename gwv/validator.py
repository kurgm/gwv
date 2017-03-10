# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools

from gwv import validators


def validate(dump, validator_names=None, timestamp=None):
    if validator_names is None:
        validator_names = validators.all_validator_names
    validator_modules = [getattr(validators, name) for name in validator_names]

    filternames = validators.filters.keys()

    filtered_validators = {
        k: [] for k in itertools.product(*[validators.filters[filtername] for filtername in filternames])
    }
    for mod in validator_modules:
        for k in itertools.product(*[mod.filters[filtername] for filtername in filternames]):
            filtered_validators[k].append(mod)

    filter_funcs = [validators.filter_funcs[filtername]
                    for filtername in filternames]

    for glyphname in sorted(dump.keys()):
        related, data = dump[glyphname]
        vals = filtered_validators[
            tuple(f(glyphname, related, data) for f in filter_funcs)]
        for val in vals:
            val.validate(glyphname, related, data)

    return {val.name: {
        "timestamp": timestamp,
        "result": val.get_result()
    } for val in validator_modules}
