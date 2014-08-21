# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.conf import settings as _settings

DEFAULTS = {
    'FACETS_ENABLED': not _settings.DEBUG,

    'FACETS_HANDLERS': (
        'facets.processors.css.CssUrlsProcessor',
    )
}


class FacetsSettings(object):
    def __init__(self, wrapped_settings):
        self._wrapped = wrapped_settings

    def __getattr__(self, name):
        if hasattr(self._wrapped, name):
            return getattr(self._wrapped, name)
        elif name in DEFAULTS:
            return DEFAULTS[name]
        else:
            raise AttributeError('{0} setting not found.'.format(name))

settings = FacetsSettings(_settings)
