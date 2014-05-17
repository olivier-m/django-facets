# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import csv
import os.path
import re
from urlparse import urlunsplit, urlsplit

from django.utils.encoding import force_unicode

from facets.compilers.base import CommandCompiler, Compiler, CompilerError
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
    extensions = ('less',)
    new_name = '{base}.css'

    program = '/usr/bin/env lessc'
    command = '{program} - {outfile}'

    def __init__(self, *args, **kwargs):
        super(LessCompiler, self).__init__(*args, **kwargs)
        self._dependencies = None
        self._contents = None

    def _set_contents(self):
        with open(self.original, 'r') as fp:
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

        self.execute_cmd(data=self._contents, outfile=self.storage.path(self.new_name))
        return self.new_name


#
class SassImportNormalizer(UrlsNormalizer):
    patterns = (
       (re.compile(r"""^\s*(@import\s*(?P<spec>"\s*.+")\s*(?:;|$))""", re.M), '@import {spec};'),
    )

    spec_split = re.compile(r'(?<=").+?(?=")')

    def __init__(self, root_url=None):
        self.root_url = ''
        self.dependencies = set()

    def get_new_path(self, parts):
        path = super(SassImportNormalizer, self).get_new_path(parts)

        # resolve imported file with base finders
        ext = os.path.splitext(path)[1]
        directory, base = os.path.dirname(path), os.path.basename(path)

        if ext:
            lookup = [(path, False), ('{0}/_{1}'.format(directory, base), True)]
        else:
            lookup = [
                ('{0}.scss'.format(path), False), ('{0}/_{1}.scss'.format(directory, base), True),
                ('{0}.sass'.format(path), False), ('{0}/_{1}.sass'.format(directory, base), True),
            ]

        for _path, partials in lookup:
            full_path = find_in_base_finders(_path)
            if full_path:
                self.dependencies.add(full_path)
                if partials:
                    # Remove underscore if partial
                    full_path = os.path.join(
                        os.path.dirname(full_path),
                        os.path.basename(full_path)[1:]
                    )
                return full_path

        return path

    def replace(self, match, repl):
        groups = match.groups()

        # Saas @import spec is (too?) complicated. We have to split values, check for
        # magical files begining with underscore and handle two possible extensions.
        # This is a bit boring.

        # Split url list
        url_list = [x for x in csv.reader([match.group('spec')], skipinitialspace=True)][0]

        # Check extensions
        if len([x for x in url_list if os.path.splitext(x)[1] not in ('.scss', '.sass', '')]) > 0:
            return groups[0]

        new_list = []
        for url in url_list:
            parts = urlsplit(url)
            if not self.check_parts(parts):
                return groups[0]

            parts = self.rebuild_url_parts(url, parts, self.get_new_path(parts))
            new_list.append(urlunsplit(parts))

        spec = '"{0}"'.format('","'.join(new_list))
        return repl.format(spec=spec)

    def normalize(self, *args, **kwargs):
        self.dependencies = set()
        return super(SassImportNormalizer, self).normalize(*args, **kwargs)


class BaseSassCompiler(object):
    extensions = ('scss', 'sass')
    new_name = '{base}.css'

    def __init__(self, *args, **kwargs):
        super(BaseSassCompiler, self).__init__(*args, **kwargs)
        self._dependencies = None
        self._contents = None

    def _set_contents(self):
        with open(self.original, 'r') as fp:
            n = SassImportNormalizer('')
            self._contents = n.normalize(force_unicode(fp.read()), os.path.dirname(self.path))
            self._dependencies = n.dependencies

    def get_dependencies(self):
        if self._dependencies is None:
            self._set_contents()

        return self._dependencies


class SasscCompiler(BaseSassCompiler, CommandCompiler):
    program = '/usr/bin/env sassc'
    command = '{program} -'

    def compile(self):
        if self._contents is None:
            self._set_contents()

        contents = self.execute_cmd(data=self._contents)
        self.save_contents(contents)

        return self.new_name


class LibSassCompiler(BaseSassCompiler, Compiler):
    def compile(self):
        try:
            import sass
        except ImportError:
            raise CompilerError('Unable to import sass module.')

        if self._contents is None:
            self._set_contents()

        contents = sass.compile(string=self._contents)
        self.save_contents(contents)

        return self.new_name
