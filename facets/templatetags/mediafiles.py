# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
from urlparse import urljoin

import html5lib
from html5lib import sanitizer

from django import template
from django.conf import settings

from facets.store import media_store
from facets.collections import MediaCollection, CollectionException

register = template.Library()

class MediaFileNode(template.Node):
    def __init__(self, path):
        self.path = path
    
    def render(self, context):
        return self.path

class MediaCollectionNode(template.Node):
    def __init__(self, nodelist, path):
        self.nodelist = nodelist
        self.path = path
    
    def render(self, context):
        output = self.nodelist.render(context)
        
        if not settings.MEDIA_CACHE_ACTIVE:
            return output
        
        collection = MediaCollection(output, media_store[self.path])
        return collection.get_html(settings.MEDIA_CACHE_URL)
    
    def resolve(self, context=None):
        context = context or template.Context()
        output = self.nodelist.render(context)
        
        return MediaCollection(output, self.path)
    

def do_mediafile(parser, token):
    try:
        tag_name, path = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    if not (path[0] == path[-1] and path[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    
    path = path[1:-1]
    if settings.MEDIA_CACHE_ACTIVE:
        if not path in media_store:
            raise template.TemplateSyntaxError("%r media file does not exist." % path)
        path = urljoin(settings.MEDIA_CACHE_URL, media_store[path])
    else:
        path = urljoin(settings.MEDIA_URL, path)
    
    return MediaFileNode(path)


def do_mediacollection(parser, token):
    try:
        tag_name, path = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    if not (path[0] == path[-1] and path[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    
    path = path[1:-1]
    
    nodelist = parser.parse(('endmediacollection',))
    parser.delete_first_token()
    return MediaCollectionNode(nodelist, path)


do_mediafile = register.tag('mediafile', do_mediafile)
do_mediacollection = register.tag('mediacollection', do_mediacollection)
