# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv import helper


class TestHelper(unittest.TestCase):

    def test_isKanji(self):
        self.assertTrue(helper.isKanji("u2ff0-u4e00-u4e01"))
        self.assertFalse(helper.isKanji("u2ff0"))
        # self.assertFalse(helper.isKanji("u2ff0-var-001"))

        self.assertTrue(helper.isKanji("u4e00"))
        self.assertTrue(helper.isKanji("u20000"))
        self.assertTrue(helper.isKanji("uf900"))
        self.assertTrue(helper.isKanji("u2f800"))
        self.assertTrue(helper.isKanji("u4e00-var-001"))
        self.assertFalse(helper.isKanji("u0020"))
        self.assertFalse(helper.isKanji("u1f600-itaiji-001"))

        self.assertTrue(helper.isKanji("koseki-000010"))
        self.assertTrue(helper.isKanji("koseki-090010"))
        self.assertFalse(helper.isKanji("koseki-900010"))
        # self.assertFalse(helper.isKanji("koseki-900010-var-001"))

        self.assertTrue(helper.isKanji("sandbox"))
        self.assertTrue(helper.isKanji("twe_u0020"))
        self.assertTrue(helper.isKanji("some-unknown-name"))

    def test_isTogoKanji(self):
        self.assertFalse(helper.isTogoKanji("u4dff"))
        self.assertTrue(helper.isTogoKanji("u4e00"))
        self.assertTrue(helper.isTogoKanji("u9fea"))
        self.assertFalse(helper.isTogoKanji("u9feb"))
        self.assertFalse(helper.isTogoKanji("u9fff"))

        self.assertFalse(helper.isTogoKanji("u33ff"))
        self.assertTrue(helper.isTogoKanji("u3400"))
        self.assertTrue(helper.isTogoKanji("u4db5"))
        self.assertFalse(helper.isTogoKanji("u4db6"))
        self.assertFalse(helper.isTogoKanji("u4dc0"))

        self.assertFalse(helper.isTogoKanji("u14e00"))

        self.assertFalse(helper.isTogoKanji("u1ffff"))
        self.assertTrue(helper.isTogoKanji("u20000"))
        self.assertTrue(helper.isTogoKanji("u2a6d6"))
        self.assertFalse(helper.isTogoKanji("u2a6d7"))
        self.assertFalse(helper.isTogoKanji("u2a6e0"))

        self.assertFalse(helper.isTogoKanji("u2a6ff"))
        self.assertTrue(helper.isTogoKanji("u2a700"))
        self.assertTrue(helper.isTogoKanji("u2b734"))
        self.assertFalse(helper.isTogoKanji("u2b735"))

        self.assertFalse(helper.isTogoKanji("u2b73f"))
        self.assertTrue(helper.isTogoKanji("u2b740"))
        self.assertTrue(helper.isTogoKanji("u2b81d"))
        self.assertFalse(helper.isTogoKanji("u2b81e"))

        self.assertFalse(helper.isTogoKanji("u2b81f"))
        self.assertTrue(helper.isTogoKanji("u2b820"))
        self.assertTrue(helper.isTogoKanji("u2cea1"))
        self.assertFalse(helper.isTogoKanji("u2cea2"))

        self.assertFalse(helper.isTogoKanji("u2ceaf"))
        self.assertTrue(helper.isTogoKanji("u2ceb0"))
        self.assertTrue(helper.isTogoKanji("u2ebe0"))
        self.assertFalse(helper.isTogoKanji("u2ebe1"))
        self.assertFalse(helper.isTogoKanji("u2ebff"))

        self.assertFalse(helper.isTogoKanji("uf900"))
        self.assertEqual(
            [helper.isTogoKanji("u{:04x}".format(c))
             for c in xrange(0xfa00, 0xfa2f + 1)],
            [
                False, False, False, False, False, False, False, False,
                False, False, False, False, False, False, True, True,
                False, True, False, True, True, False, False, False,
                False, False, False, False, False, False, False, True,
                False, True, False, True, True, False, False, True,
                True, True, False, False, False, False, False, False,
            ])
        self.assertFalse(helper.isTogoKanji("ufad9"))
        self.assertFalse(helper.isTogoKanji("ufada"))

        self.assertFalse(helper.isTogoKanji("u2f800"))
        self.assertFalse(helper.isTogoKanji("u2fa1d"))
        self.assertFalse(helper.isTogoKanji("u2fa1e"))

        self.assertFalse(helper.isTogoKanji("u0020"))

    def test_isGokanKanji(self):
        self.assertFalse(helper.isGokanKanji("u4e00"))
        self.assertFalse(helper.isGokanKanji("u3400"))
        self.assertFalse(helper.isGokanKanji("u20000"))
        self.assertFalse(helper.isGokanKanji("u2a700"))
        self.assertFalse(helper.isGokanKanji("u2b740"))
        self.assertFalse(helper.isGokanKanji("u2b820"))
        self.assertFalse(helper.isGokanKanji("u2ceb0"))

        self.assertFalse(helper.isGokanKanji("uf8ff"))
        self.assertTrue(helper.isGokanKanji("uf900"))
        self.assertEqual(
            [helper.isGokanKanji("u{:04x}".format(c))
             for c in xrange(0xfa00, 0xfa2f + 1)],
            [
                True, True, True, True, True, True, True, True,
                True, True, True, True, True, True, False, False,
                True, False, True, False, False, True, True, True,
                True, True, True, True, True, True, True, False,
                True, False, True, False, False, True, True, False,
                False, False, True, True, True, True, True, True,
            ])
        self.assertTrue(helper.isGokanKanji("ufa6d"))
        self.assertFalse(helper.isGokanKanji("ufa6e"))

        self.assertFalse(helper.isGokanKanji("ufa6f"))
        self.assertTrue(helper.isGokanKanji("ufa70"))
        self.assertTrue(helper.isGokanKanji("ufad9"))
        self.assertFalse(helper.isGokanKanji("ufada"))
        self.assertFalse(helper.isGokanKanji("ufaff"))

        self.assertFalse(helper.isGokanKanji("u2f7ff"))
        self.assertTrue(helper.isGokanKanji("u2f800"))
        self.assertTrue(helper.isGokanKanji("u2f9ff"))
        self.assertTrue(helper.isGokanKanji("u2fa1d"))
        self.assertFalse(helper.isGokanKanji("u2fa1e"))

        self.assertFalse(helper.isGokanKanji("u0020"))

    def test_isUcs(self):
        self.assertTrue(helper.isUcs("u0000"))
        self.assertTrue(helper.isUcs("u10000"))
        self.assertTrue(helper.isUcs("u100000"))
        self.assertTrue(helper.isUcs("u2ff0"))

        self.assertFalse(helper.isUcs("u0000-var-001"))
        self.assertFalse(helper.isUcs("u0000-itaiji-001"))
        self.assertFalse(helper.isUcs("u2ff0-u4e00-u4e01"))
        self.assertFalse(helper.isUcs("undefined"))
        self.assertFalse(helper.isUcs("twe_u0020"))

    def test_isYoko(self):
        self.assertTrue(helper.isYoko(12, 100, 188, 100))
        self.assertFalse(helper.isYoko(100, 12, 100, 188))

        self.assertFalse(helper.isYoko(12, 100, 100, 12))
        self.assertTrue(helper.isYoko(12, 100, 100, 13))
        self.assertFalse(helper.isYoko(12, 100, 100, 188))
        self.assertTrue(helper.isYoko(12, 100, 100, 187))

        self.assertFalse(helper.isYoko(188, 100, 12, 99))
        self.assertTrue(helper.isYoko(188, 100, 12, 100))
        self.assertFalse(helper.isYoko(188, 100, 12, 101))

        self.assertFalse(helper.isYoko(100, 188, 100, 12))

    def test_GWGroupLazyLoader(self):
        loader = helper.GWGroupLazyLoader("kamichi_test@27")
        data = loader.get_data()
        self.assertEqual(data, [
            "u908a", "u908a-ue0100", "u908a-ue0101", "u908a-ue0102",
            "u908a-ue0103", "u908a-ue0104", "u908a-ue0105"
        ])
        # test caching
        data2 = loader.get_data()
        self.assertIs(data, data2)

        loader = helper.GWGroupLazyLoader("kamichi_test@37", isset=True)
        data = loader.get_data()
        self.assertEqual(data, {"kamichi_test-001"})
        # test caching
        data2 = loader.get_data()
        self.assertIs(data, data2)
