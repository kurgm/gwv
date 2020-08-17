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
