# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from django.conf import settings
from django.conf.urls import patterns


def facets_urlpatterns(**options):
    options.update({
        'document_root': settings.STATIC_ROOT
    })

    return patterns('django.views.static',
        (r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'serve', options),
    )
