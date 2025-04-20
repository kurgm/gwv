import unittest

from gwv import helper


class TestHelper(unittest.TestCase):
    def test_isYoko(self):
        self.assertTrue(helper.isYoko(12, 100, 188, 100))
