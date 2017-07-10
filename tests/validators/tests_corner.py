# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gwv.validators import corner

from .validator_tester import ValidatorTestCase


class TestCornerValidator(ValidatorTestCase):

    validator_class = corner.validator_class

    # TODO
