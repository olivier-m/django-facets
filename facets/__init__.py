# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from django.conf import settings

from .version import __version__

__HANDLERS = (
    'facets.handlers.CssUrls',
)

setattr(settings, 'FACETS_ACTIVE', getattr(settings,
    'FACETS_ACTIVE', not settings.DEBUG
))

setattr(settings, 'FACETS_HANDLERS', getattr(settings,
    'FACETS_HANDLERS', __HANDLERS
))
