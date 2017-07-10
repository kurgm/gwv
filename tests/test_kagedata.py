# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv import kagedata


class TestKagedata(unittest.TestCase):

    def test_kageInt(self):
        self.assertEqual(kagedata.kageInt("42"), 42)
        self.assertEqual(kagedata.kageInt("010"), 10)
        self.assertEqual(kagedata.kageInt("-42"), -42)
        self.assertEqual(kagedata.kageInt("-010"), -10)
        self.assertEqual(kagedata.kageInt("10.24"), 10)
        self.assertEqual(kagedata.kageInt("-010.24"), -11)
        self.assertEqual(kagedata.kageInt("  -010.24\t"), -11)
        self.assertEqual(kagedata.kageInt("0x10"), 16)
        self.assertEqual(kagedata.kageInt(" \t -0x10\n \r"), -16)
        self.assertEqual(kagedata.kageInt("0o10"), 8)
        self.assertEqual(kagedata.kageInt("0b10"), 2)
        self.assertEqual(kagedata.kageInt(""), 0)
        self.assertEqual(kagedata.kageInt(" "), 0)
        self.assertEqual(kagedata.kageInt(" -0 "), 0)

    def test_kageIntSuppressError(self):
        self.assertEqual(kagedata.kageIntSuppressError("  -0  "), 0)

        with self.assertRaises(ValueError):
            kagedata.kageInt("abc")
        self.assertEqual(kagedata.kageIntSuppressError("abc"), None)

        with self.assertRaises(ValueError):
            kagedata.kageInt("0b2")
        self.assertEqual(kagedata.kageIntSuppressError("0b2"), None)

        with self.assertRaises(ValueError):
            kagedata.kageInt("0x10.24")
        self.assertEqual(kagedata.kageIntSuppressError("0x10.24"), None)

        with self.assertRaises(OverflowError):
            kagedata.kageInt("inf")
        self.assertEqual(kagedata.kageIntSuppressError("inf"), None)

        with self.assertRaises(OverflowError):
            kagedata.kageInt("-inf")
        self.assertEqual(kagedata.kageIntSuppressError("-inf"), None)

    def test_KageData(self):
        kage = kagedata.KageData("0:0:0:0")
        self.assertEqual(kage.len, 1)
        self.assertEqual(len(kage.lines), 1)
        self.assertFalse(kage.isAlias())
        self.assertFalse(kage.isAlias())  # to test caching
        line = kage.lines[0]
        self.assertEqual(line.line_number, 0)
        self.assertEqual(line.strdata, "0:0:0:0")

        kage = kagedata.KageData("99:0:0:0:0:200:200:u4e00")
        self.assertEqual(kage.len, 1)
        self.assertEqual(len(kage.lines), 1)
        self.assertTrue(kage.isAlias())
        self.assertTrue(kage.isAlias())  # to test caching
        line = kage.lines[0]
        self.assertEqual(line.line_number, 0)
        self.assertEqual(line.strdata, "99:0:0:0:0:200:200:u4e00")

        kage = kagedata.KageData("6:22:32:10:30:50:70:90:110:130:150$7:12:7:50:60:70:80:90:100:110:120")
        self.assertEqual(kage.len, 2)
        self.assertEqual(len(kage.lines), 2)
        self.assertFalse(kage.isAlias())
        line = kage.lines[1]
        self.assertEqual(line.line_number, 1)
        self.assertEqual(line.strdata, "7:12:7:50:60:70:80:90:100:110:120")

    def test_KageLine(self):
        line = kagedata.KageLine(10, "0:0:0:0")
        self.assertEqual(line.line_number, 10)
        self.assertEqual(line.strdata, "0:0:0:0")
        self.assertEqual(line.data, (0, 0, 0, 0))

        line = kagedata.KageLine(11, "99:0:0:0:0:200:200:u4e00@1")
        self.assertEqual(line.line_number, 11)
        self.assertEqual(line.strdata, "99:0:0:0:0:200:200:u4e00@1")
        self.assertEqual(line.data, (99, 0, 0, 0, 0, 200, 200, "u4e00@1"))

        line = kagedata.KageLine(12, "7:12:22:32:42:52:62:72:82:92:-2")
        self.assertEqual(line.line_number, 12)
        self.assertEqual(line.strdata, "7:12:22:32:42:52:62:72:82:92:-2")
        self.assertEqual(line.data, (7, 12, 22, 32, 42, 52, 62, 72, 82, 92, -2))

        line = kagedata.KageLine(13, "")
        self.assertEqual(line.line_number, 13)
        self.assertEqual(line.strdata, "")
        self.assertEqual(line.data, (0, ))

        line = kagedata.KageLine(14, "0x63:: 0 :0x2:-0b0:abc:10.24:0:-99.12:0x10.24")
        self.assertEqual(line.line_number, 14)
        self.assertEqual(line.strdata, "0x63:: 0 :0x2:-0b0:abc:10.24:0:-99.12:0x10.24")
        self.assertEqual(line.data, (99, 0, 0, 2, 0, None, 10, "0", -100, None))
