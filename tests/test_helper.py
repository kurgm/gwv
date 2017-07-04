# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from gwv import helper


class TestHelper(unittest.TestCase):

    def test_isYoko(self):
        self.assertTrue(helper.isYoko(12, 100, 188, 100))
