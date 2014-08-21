# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import re
import shlex
from subprocess import Popen, PIPE

from django.utils.encoding import smart_str, force_bytes
from django.utils.six.moves.urllib.parse import urljoin, urlsplit, urlunsplit

from facets.conf import settings


class CommandError(Exception):
    pass


class UrlsNormalizer(object):
    patterns = (
        (re.compile(r"""(url\(['"]{0,1}\s*(?P<url>.*?)["']{0,1}\))"""), """url("{new}")"""),
        (re.compile(r"""(@import\s*["']\s*(?P<url>.*?)["'])"""), """@import url("{new}")"""),
    )

    def __init__(self, root_url=None):
        self.root_url = root_url or settings.STATIC_URL

    def get_replace_args(self, parts, match):
        parts = self.rebuild_url_parts(match.group('url'), parts, self.get_new_path(parts))

        return {
            'new': urlunsplit(parts)
        }

    def check_parts(self, parts):
        # Ignore URLs with scheme or netloc - http(s), data, //
        if parts.scheme or parts.netloc:
            return False

        # Return original URL if not path (could be just a fragment)
        if not parts.path:
            return False

        return True

    def rebuild_url_parts(self, original, parts, new_path):
        # Rebuild URL
        parts = list(parts)
        parts[2] = new_path

        # special case for some @font-face hacks
        if '?#' in original:
            parts[2] += '?'
            if not parts[4]:
                parts[2] += '#'
        elif original.endswith('?'):
            parts[2] += '?'
        elif original.endswith('#'):
            parts[2] += '#'

        return parts

    def get_new_path(self, parts):
        return urljoin(self.base_src, parts.path)

    def replace(self, match, repl):
        groups = match.groups()
        parts = urlsplit(match.group('url'))

        if not self.check_parts(parts):
            return groups[0]

        kwargs = self.get_replace_args(parts, match)

        return repl.format(**kwargs)

    def normalize(self, content, location):
        self.base_src = urljoin(self.root_url, location)
        if not self.base_src.endswith('/'):
            self.base_src += '/'

        for pattern, repl in self.patterns:
            rep_func = lambda m: self.replace(m, repl)
            content = pattern.sub(rep_func, content)

        return content


class CssDependencies(UrlsNormalizer):
    def __init__(self, root_url=None):
        super(CssDependencies, self).__init__(root_url)
        self.dependencies = {}

    def get_new_path(self, parts):
        path = super(CssDependencies, self).get_new_path(parts)
        if path.startswith(self.root_url):
            key = path[len(self.root_url):]
            if key not in self.dependencies:
                self.dependencies[key] = set([self.key_name])
            else:
                self.dependencies[key].add(self.key_name)

        return path

    def normalize(self, content, location, key_name):
        self.key_name = key_name
        return super(CssDependencies, self).normalize(content, location)


class CommandHandlerMixin(object):
    command = None
    program = None

    def execute_cmd(self, infile=None, outfile=None, data=None, **kwargs):
        if not self.program:
            raise CommandError('No program provided')

        if not self.command:
            raise CommandError('No command provided')

        cmd = self.command.format(program=self.program, infile=infile, outfile=outfile, **kwargs)

        try:
            cmd = shlex.split(smart_str(cmd))
            p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except OSError as e:
            raise CommandError('OSError on command: {0}'.format(str(e)))
        else:
            out, err = p.communicate(force_bytes(data))
            if p.returncode != 0:
                raise CommandError('Command error: {0}'.format(err))

            return out
