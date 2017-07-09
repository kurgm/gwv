# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv.kagedata import KageData


class ValidatorTestCase(unittest.TestCase):

    def assertValidatorErrors(self, dump, errors, msg=None):
        validator = self.validator_class()
        for glyphname in sorted(dump.keys()):
            related, data = dump[glyphname]
            kage = KageData(data)
            validator.validate(glyphname, related, kage, data, dump)
        result = validator.get_result()
        self.assertEqual(result, errors, msg=msg)

    def assertValidatorNoError(self, dump, msg=None):
        self.assertValidatorErrors(dump, {}, msg=msg)
