# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv import validators


class TestValidators(unittest.TestCase):

    def test__categorize(self):
        self.assertEqual(
            validators._categorize("twe_sandbox"),
            "user-owned")

        self.assertEqual(
            validators._categorize("u2ff0-u4e00-u4e01"),
            "ids")
        self.assertEqual(
            validators._categorize("u2ff9-u4e00-u4e01-var-001"),
            "ids")
        self.assertEqual(
            validators._categorize("u2ffb-u4e00-u4e01-itaiji-009"),
            "ids")
        self.assertEqual(
            validators._categorize("u2ff0-u4e00"),  # invalid IDS
            "ids")
        self.assertEqual(
            validators._categorize("u2ff0"),
            "ucs-hikanji")
        # self.assertEqual(
        #     validators._categorize("u2ff0-var-001"),
        #     "ucs-hikanji-var")

        self.assertEqual(
            validators._categorize("u4e00"),
            "togo")
        self.assertEqual(
            validators._categorize("u9fea"),
            "togo")
        self.assertEqual(
            validators._categorize("u3400"),
            "togo")
        self.assertEqual(
            validators._categorize("u2ebe0"),
            "togo")
        self.assertEqual(
            validators._categorize("ufa0e"),
            "togo")

        self.assertEqual(
            validators._categorize("u4e00-01"),
            "togo-var")
        self.assertEqual(
            validators._categorize("u4e00-var-001"),
            "togo-var")
        self.assertEqual(
            validators._categorize("u4e00-itaiji-001"),
            "togo-var")
        self.assertEqual(
            validators._categorize("u4e00-foobarbaz"),
            "togo-var")

        self.assertEqual(
            validators._categorize("uf900"),
            "gokan")
        self.assertEqual(
            validators._categorize("ufad9"),
            "gokan")
        self.assertEqual(
            validators._categorize("u2f800"),
            "gokan")
        self.assertEqual(
            validators._categorize("u2fa1d"),
            "gokan")
        self.assertEqual(
            validators._categorize("ufa0d"),
            "gokan")

        self.assertEqual(
            validators._categorize("uf900-var-001"),
            "gokan-var")

        self.assertEqual(
            validators._categorize("u0020"),
            "ucs-hikanji")
        self.assertEqual(
            validators._categorize("u1f600"),
            "ucs-hikanji")

        self.assertEqual(
            validators._categorize("u0020-var-001"),
            "ucs-hikanji-var")

        self.assertEqual(
            validators._categorize("cdp-854b"),
            "cdp")
        self.assertEqual(
            validators._categorize("cdp-854b-var-001"),
            "cdp")
        self.assertEqual(
            validators._categorize("cdpo-854b-itaiji-001"),
            "cdp")
        self.assertEqual(
            validators._categorize("cdpn-854b-foobarbaz"),
            "cdp")

        self.assertEqual(
            validators._categorize("koseki-000010"),
            "koseki-kanji")
        self.assertEqual(
            validators._categorize("koseki-899990"),
            "koseki-kanji")
        self.assertEqual(
            validators._categorize("koseki-000010-var-001"),
            "other")

        self.assertEqual(
            validators._categorize("koseki-900010"),
            "koseki-hikanji")
        self.assertEqual(
            validators._categorize("koseki-907730"),
            "koseki-hikanji")
        self.assertEqual(
            validators._categorize("koseki-000010-var-001"),
            "other")

        self.assertEqual(
            validators._categorize("toki-00000010"),
            "toki")
        self.assertEqual(
            validators._categorize("toki-01000010"),
            "toki")
        self.assertEqual(
            validators._categorize("toki-00000010-var-001"),
            "other")

        self.assertEqual(
            validators._categorize("extf-00001"),
            "ext")
        self.assertEqual(
            validators._categorize("irg2015-00001"),
            "ext")
        self.assertEqual(
            validators._categorize("extf-00001-var-001"),
            "other")

        self.assertEqual(
            validators._categorize("sandbox"),
            "other")
        self.assertEqual(
            validators._categorize("some-glyph-that-does-not-exist"),
            "other")

    def test_ErrorCodes(self):
        with self.assertRaises(AssertionError):
            validators.ErrorCodes(
                A="1",
                B="1",
            )

        error_codes = validators.ErrorCodes(
            A="1",
            B="2",
        )
        self.assertEqual(error_codes.A, "1")
        self.assertEqual(error_codes.B, "2")
        self.assertEqual(error_codes["1"], "A")
        self.assertEqual(error_codes["2"], "B")
