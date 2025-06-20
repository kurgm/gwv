from __future__ import annotations

import unittest

from gwv import validator, validators
from gwv.dump import Dump


class TestValidator(unittest.TestCase):
    def test_validateEmpty(self):
        timestamp = 334.0
        expected_output = {
            name: {"timestamp": timestamp, "result": {}}
            for name in validators.all_validator_names
        }
        expected_output["mustrenew"]["result"] = {
            "@": [],
            "0": [],
        }

        dump = Dump({}, timestamp)
        self.assertEqual(validator.validate(dump), expected_output)
