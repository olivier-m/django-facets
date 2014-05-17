# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path
import re

from django.utils.encoding import force_unicode

from facets.compilers.base import CommandCompiler
from facets.finders import find_in_base_finders
from facets.utils import UrlsNormalizer


class LessImportNormalizer(UrlsNormalizer):
    patterns = (
       (re.compile(r"""(@import\s*(?P<kw>\([a-z]+\))?\s*["']\s*(?P<url>.*?)["'])"""), '@import {kw}"{new}"'),
    )

    def __init__(self, root_url=None):
        self.root_url = ''
        self.dependencies = set()

    def get_replace_args(self, parts, match):
        kw = match.group('kw')
        args = super(LessImportNormalizer, self).get_replace_args(parts, match)
        args.update({
            'kw': kw and kw + ' ' or ''
        })
        return args

    def replace(self, match, repl):
        # Don't process @imports with .css
        if match.group('url').endswith('.css'):
            return match.groups()[0]

        # Don't proccess @import with (css) option
        if match.group('kw') == '(css)':
            return match.groups()[0]

        return super(LessImportNormalizer, self).replace(match, repl)

    def get_new_path(self, parts):
        path = super(LessImportNormalizer, self).get_new_path(parts)

        # resolve imported file with base finders
        full_path = find_in_base_finders(path)
        if not full_path and not path.endswith('.less'):
            full_path = find_in_base_finders('{0}.less'.format(path))

        if full_path:
            self.dependencies.add(full_path)

        return full_path or path

    def normalize(self, *args, **kwargs):
        self.dependencies = set()
        return super(LessImportNormalizer, self).normalize(*args, **kwargs)


class LessCompiler(CommandCompiler):
    extension = 'less'
    new_name = '{base}.css'

    program = '/usr/bin/env lessc'
    command = '{program} - {outfile}'

    def __init__(self, *args, **kwargs):
        super(LessCompiler, self).__init__(*args, **kwargs)
        self._dependencies = None
        self._contents = None

    def _set_contents(self):
        with open(self.original) as fp:
            n = LessImportNormalizer('')
            self._contents = n.normalize(force_unicode(fp.read()), os.path.dirname(self.path))
            self._dependencies = n.dependencies

    def get_dependencies(self):
        if self._dependencies is None:
            self._set_contents()

        return self._dependencies

    def compile(self):
        if self._contents is None:
            self._set_contents()

        self.execute_cmd(
            infile=self.original, outfile=self.storage.path(self.new_name),
            data=self._contents
        )
        return self.new_name
