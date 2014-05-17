# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.core.cache import get_cache, InvalidCacheBackendError, cache as default_cache
from django.utils.functional import SimpleLazyObject


def facets_cache():
    try:
        return get_cache('facets')
    except InvalidCacheBackendError:
        return default_cache


cache = SimpleLazyObject(facets_cache)
