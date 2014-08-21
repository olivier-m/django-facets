# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from StringIO import StringIO
import hashlib
import os.path

import html5lib
from html5lib import treebuilders

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django import template
from django.utils.encoding import force_str

from facets.utils import UrlsNormalizer


def _attr_data(data):
    data = data.replace("&", "&amp;").replace("<", "&lt;")
    data = data.replace("\"", "&quot;").replace(">", "&gt;")
    return data


class CollectionException(Exception):
    pass


class MediaCollectionList(set):
    def check_path(self, element):
        by_path = dict([(x.path, x) for x in self])
        if element.path in by_path and not(element == by_path[element.path]):
            raise CollectionException(
                'A collection named "%s" already exists with a different content' % element.path
            )

    def add(self, element):
        self.check_path(element)
        super(MediaCollectionList, self).add(element)

    def update(self, iterable):
        [self.check_path(x) for x in iterable]
        super(MediaCollectionList, self).update(iterable)


class MediaCollection(object):
    def __init__(self, data, path):
        parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
        node = parser.parseFragment(data)
        self.node = node
        self.path = path
        self.init_collection()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and hash(self) == hash(other)

    def __hash__(self):
        m = hashlib.md5()
        [m.update(x) for x in self.media]
        m.update(self.path)
        return int(m.hexdigest(), 16)

    def clear(self):
        self.type = None
        self.attrs = {}
        self.media = []

    def init_collection(self):
        self.clear()
        for n in self.node.childNodes:
            if n.nodeType == n.TEXT_NODE:
                continue
            if n.nodeType != n.ELEMENT_NODE:
                raise CollectionException('Collection should not contain non element nodes.')

            name = n.nodeName.lower()
            if self.type and self.type != name:
                raise CollectionException(
                    'Collection should contain elements of type {0} only.'.format(self.type)
                )

            self.type = name

            if name == 'link':
                self.set_prop_link(n)
            elif name == 'script':
                self.set_prop_script(n)

    def attr_value(self, node, name, default=None):
        attr = node.attributes.get(name)
        if attr is None:
            return default

        return attr.value

    def set_prop_link(self, node):
        rel = self.attr_value(node, 'rel')
        href = self.attr_value(node, 'href')
        ctype = self.attr_value(node, 'type', 'text/css')
        media = self.attr_value(node, 'media', 'screen')

        if self.attrs.get('rel') not in (None, rel):
            raise CollectionException('All rel attributes should be the same in collection.')
        if self.attrs.get('type') not in (None, ctype):
            raise CollectionException('All type attributes should be the same in collection.')
        if self.attrs.get('media') not in (None, media):
            raise CollectionException('All media attributes should be the same in collection.')

        self.attrs.update({
            'rel': rel, 'type': ctype, 'media': media
        })

        self.media.append(href)

    def set_prop_script(self, node):
        ctype = self.attr_value(node, 'type', 'text/javascript')
        src = self.attr_value(node, 'src')

        if src is None:
            raise CollectionException('No src attribute in collection script tag.')
        if self.attrs.get('type') not in (None, ctype):
            raise CollectionException('All type attributes should be the same in collection.')

        self.attrs.update({
            'type': ctype,
        })

        self.media.append(src)

    def get_html(self):
        if self.type == 'link':
            return self.get_html_link()
        elif self.type == 'script':
            return self.get_html_script()

    def get_html_link(self):
        attrs = dict(self.attrs)
        attrs['href'] = staticfiles_storage.url(self.path)
        tag = '<link %s />'
        return tag % ' '.join(
            ['%s="%s"' % (k, _attr_data(v)) for k, v in attrs.items()]
        )

    def get_html_script(self):
        attrs = dict(self.attrs)
        attrs['src'] = staticfiles_storage.url(self.path)
        tag = '<script %s></script>'
        return tag % ' '.join(
            ['%s="%s"' % (k, _attr_data(v)) for k, v in attrs.items()]
        )

    def get_data(self):
        out = StringIO()

        for x in self.media:
            if not x.startswith(staticfiles_storage.base_url):
                raise CollectionException("Collection contains a non static file.")

            path = x[len(staticfiles_storage.base_url):]
            filename = staticfiles_storage.path(path)

            with open(filename, 'rb') as fp:
                data = force_str(fp.read())

                if self.type == "link" and self.attrs.get("type") == "text/css":
                    data = UrlsNormalizer().normalize(data, os.path.dirname(path))
                elif self.type == "script":
                    data = "(function() {\n%s\n})();" % data

                out.write(data)
                out.write("\n")

        return out.getvalue()


def get_loaders():
    def chain(root):
        if isinstance(root, (list, tuple)):
            for el in root:
                for e in chain(el):
                    yield e
        else:
            yield root

    return list(chain(settings.TEMPLATE_LOADERS))


def parse_templates():
    # Most parts of this code comes from django assets
    #
    template_dirs = []
    loaders = get_loaders()

    if 'django.template.loaders.filesystem.Loader' in loaders:
        template_dirs.extend(settings.TEMPLATE_DIRS)
    if 'django.template.loaders.app_directories.Loader' in loaders:
        from django.template.loaders.app_directories import app_template_dirs
        template_dirs.extend(app_template_dirs)

    for template_dir in template_dirs:
        for directory, _ds, files in os.walk(template_dir):
            for filename in files:
                if filename.endswith('.html'):
                    tmpl_path = os.path.join(directory, filename)
                    try:
                        yield parse_template(tmpl_path)
                    except Exception as e:
                        yield e


def parse_template(tmpl_path):
    from facets.templatetags.facets import MediaCollectionNode

    with open(tmpl_path, 'rb') as fp:
        contents = fp.read()

    try:
        t = template.Template(contents)
    except template.TemplateSyntaxError as e:
        raise Exception("django parser failed, error was: %s (%s)" % (str(e), tmpl_path))
    else:
        result = set()

        def _recurse_node(node):
            # depending on whether the template tag is added to
            # builtins, or loaded via {% load %}, it will be
            # available in a different module
            if isinstance(node, MediaCollectionNode):
                # try to resolve this node's data; if we fail,
                # then it depends on view data and we cannot
                # manually rebuild it.
                try:
                    collection = node.resolve()
                except template.VariableDoesNotExist:
                    raise Exception(
                        'skipping collection {0}, depends on runtime data.'.format(node.output)
                    )
                else:
                    result.add(collection)
            # see Django #7430
            for subnode in hasattr(node, 'nodelist') and node.nodelist or []:
                _recurse_node(subnode)

        for node in t:  # don't move into _recurse_node, ``Template`` has a .nodelist attribute
            _recurse_node(node)

        return result
