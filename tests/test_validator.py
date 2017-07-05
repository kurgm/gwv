# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv import validator
from gwv import validators


class TestValidator(unittest.TestCase):

    def test_validateEmpty(self):
        timestamp = 334
        expected_output = {
            name: {
                "timestamp": timestamp,
                "result": {}
            }
            for name in validators.all_validator_names
        }
        expected_output["mustrenew"]["result"] = {
            "@": [],
            "0": [],
        }
        self.assertEqual(
            validator.validate({}, timestamp=timestamp),
            expected_output
        )
