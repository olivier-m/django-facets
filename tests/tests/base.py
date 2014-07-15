# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os
from shutil import rmtree

from django.conf import settings
import django.test


class TestCase(django.test.TestCase):
    def setUp(self):
        # Reset handler list
        from facets.handlers import default_handlers
        default_handlers._setup()

    def tearDown(self):
        # Empty STATIC_ROOT
        for path in os.listdir(settings.STATIC_ROOT):
            rmtree(os.path.join(settings.STATIC_ROOT, path))
