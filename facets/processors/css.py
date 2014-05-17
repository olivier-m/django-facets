# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path
from urlparse import urljoin

from facets.processors.base import CommandProcessor, Processor, ProcessorError
from facets.utils import UrlsNormalizer


class UrlsReplacer(UrlsNormalizer):
    def __init__(self, media_store, root_url=None):
        super(UrlsReplacer, self).__init__(root_url)
        self.media_store = media_store

    def get_new_path(self, parts):
        path = super(UrlsReplacer, self).get_new_path(parts)
        if path.startswith(self.root_url):
            key = path[len(self.root_url):]
            if key in self.media_store:
                return urljoin(self.root_url, self.media_store[key])

        return path


class CssUrlsProcessor(Processor):
    match = r'\.css$'
    priority = -1000

    def process(self):
        self.save_contents(
            UrlsReplacer(self.media_store).normalize(self.read(), os.path.dirname(self.path))
        )


class CssMinProcessor(Processor):
    match = r'\.css$'

    def process(self):
        try:
            from cssmin import cssmin
        except ImportError:
            raise ProcessorError('Unable to import cssmin module.')

        self.save_contents(cssmin(self.read()))


class YuiCssProcessor(CommandProcessor):
    match = r'\.css$'

    program = '/usr/bin/env java -jar /path/to/yuicompressor-xxx.jar'
    command = '{program} {infile}'

    def process(self):
        contents = self.execute_cmd(infile=self.storage.path(self.path))
        self.save_contents(contents)
