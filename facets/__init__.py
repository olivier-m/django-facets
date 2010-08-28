# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
import os.path

from django.conf import settings

__HANDLERS = {
    'css': (
        'facets.handlers.CssUrls',
        'facets.handlers.CssMin',
    ),
    'js': (
        'facets.handlers.UglifyJs',
    ),
}

setattr(settings, 'MEDIA_CACHE_ACTIVE', getattr(settings,
    'MEDIA_CACHE_ACTIVE', False
))

setattr(settings, 'MEDIA_CACHE_ROOT', getattr(settings,
    'MEDIA_CACHE_ROOT', None
))

setattr(settings, 'MEDIA_CACHE_URL', getattr(settings,
    'MEDIA_CACHE_URL', settings.MEDIA_URL
))

setattr(settings, 'MEDIA_CACHE_STORE', getattr(settings,
    'MEDIA_CACHE_STORE',
    settings.MEDIA_CACHE_ROOT and os.path.join(settings.MEDIA_CACHE_ROOT, 'store.py') or None
))

setattr(settings, 'MEDIA_CACHE_HANDLERS', getattr(settings,
    'MEDIA_CACHE_HANDLERS', __HANDLERS
))

setattr(settings, 'MEDIA_CACHE_UGLIFYJS', getattr(settings,
    'MEDIA_CACHE_UGLIFYJS', None
))
