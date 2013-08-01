# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from django import template
from django.conf import settings

from ..collections import MediaCollection

register = template.Library()


class MediaCollectionNode(template.Node):
    def __init__(self, nodelist, path):
        self.nodelist = nodelist
        self.path = path

    def render(self, context):
        output = self.nodelist.render(context)

        if not settings.FACETS_ACTIVE:
            return output

        collection = MediaCollection(output, self.path)
        return collection.get_html()

    def resolve(self, context=None):
        context = context or template.Context()
        output = self.nodelist.render(context)

        return MediaCollection(output, self.path)


def mediacollection_node(parser, token):
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


mediacollection_node = register.tag('mediacollection', mediacollection_node)
