# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path
from tempfile import mkdtemp
from shutil import rmtree
import sys
import warnings

warnings.simplefilter('always')

from django.conf import settings

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, ROOT)
sys.path.insert(1, os.path.join(ROOT, 'tests'))

try:
    from django.utils.functional import empty
except ImportError:
    empty = None


def setup_test_environment():
    # reset settings
    settings._wrapped = empty

    settings_dict = {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            },
        },
        'INSTALLED_APPS': [
            'facets',
            'appA',
            'appB',
        ],
        'MIDDLEWARE_CLASSES': (
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        'ROOT_URLCONF': 'urls',
        'STATICFILES_FINDERS': (
            'facets.finders.FacetsFinder',
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        ),
        'STATICFILES_DIRS': (os.path.join(ROOT, 'tests/static'),),
        'STATIC_URL': '/static/',
        'STATIC_ROOT': mkdtemp()
    }

    settings.configure(**settings_dict)


def runtests():
    setup_test_environment()

    try:
        from django.test.runner import DiscoverRunner as TestRunner
        test_args = ['tests']
    except ImportError:  # Django < 1.6
        from django.test.simple import DjangoTestSuiteRunner as TestRunner
        settings.INSTALLED_APPS += ['tests']
        test_args = ['tests']

    runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    failures = runner.run_tests(test_args)
    rmtree(settings.STATIC_ROOT)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
