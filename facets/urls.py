# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns


def facets_urlpatterns(**options):
    options.update({
        'document_root': settings.STATIC_ROOT
    })

    return patterns('django.views.static',
        (r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'serve', options),
    )
