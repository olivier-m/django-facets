# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
import re
from urlparse import urljoin, urlsplit, urlunsplit

from django.conf import settings

CSS_URL_PATTERNS = (
    (re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))"""), """url("{0}")"""),
    (re.compile(r"""(@import\s*["']\s*(.*?)["'])"""), """@import url("{0}")"""),
)


def normalize_css_urls(content, basedir, path_callback=None):
    """
    Transform all URLs in a CSS content as absolute paths.
    """
    def adapt_css_url(match, repl):
        groups = list(match.groups())
        original = groups[1]

        # Ignore HTTP URLs, data-uri and fragments
        parts = urlsplit(original)

        # Ignore URLs with scheme or netloc - http(s), data, //
        if parts.scheme or parts.netloc:
            return groups[0]

        # Return original URL if not path (could be just a fragment)
        if not parts.path:
            return groups[0]

        new_path = urljoin(base_src, parts.path)

        if callable(path_callback):
            new_path = path_callback(new_path)

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

        return repl.format(urlunsplit(parts))

    base_src = urljoin(settings.STATIC_URL, basedir)
    if not base_src.endswith("/"):
        base_src += "/"

    for pattern, repl in CSS_URL_PATTERNS:
        rep_func = lambda match: adapt_css_url(match, repl)
        content = pattern.sub(rep_func, content)

    return content
