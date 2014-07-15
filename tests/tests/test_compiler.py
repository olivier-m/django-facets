# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import re

from django.test.utils import override_settings

from .base import TestCase

RE_SPACES = re.compile('\s', re.S)


def drop_spaces(v):
    return RE_SPACES.sub('', v)


@override_settings(FACETS_ENABLED=False, FACETS_HANDLERS=('facets.compilers.css.LessCompiler',))
class LessTestCase(TestCase):
    def test_basic(self):
        r = self.client.get('/static/less/basic.less')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(drop_spaces(r.content), 'body{color:#ff0000;}')

    def test_deps(self):
        r = self.client.get('/static/less/deps.less')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            drop_spaces(r.content),
            'body{background:#ffffff;color:#008000;padding:2px;}'
        )


@override_settings(FACETS_ENABLED=False, FACETS_HANDLERS=('facets.compilers.css.SasscCompiler',))
class SasscTestCase(TestCase):
    def test_basic(self):
        r = self.client.get('/static/sass/basic.scss')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(drop_spaces(r.content), 'body{color:red;}')

    def test_deps(self):
        r = self.client.get('/static/sass/deps.scss')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            drop_spaces(r.content),
            'body{background:white;color:green;padding:2px;}'
        )


@override_settings(FACETS_ENABLED=False, FACETS_HANDLERS=('facets.compilers.css.LibSassCompiler',))
class LibSassTestCase(TestCase):
    def test_basic(self):
        r = self.client.get('/static/sass/basic.scss')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(drop_spaces(r.content), 'body{color:red;}')

    def test_deps(self):
        r = self.client.get('/static/sass/deps.scss')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            drop_spaces(r.content),
            'body{background:white;color:green;padding:2px;}'
        )


@override_settings(FACETS_ENABLED=False, FACETS_HANDLERS=('facets.compilers.css.StylusCompiler',))
class StylusTestCase(TestCase):
    def test_basic(self):
        r = self.client.get('/static/styl/basic.styl')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(drop_spaces(r.content), 'body{color:#f00;}')

    def test_deps(self):
        r = self.client.get('/static/styl/deps.styl')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            drop_spaces(r.content),
            'body{background:#fff;color:#008000;padding:2px;}'
        )
