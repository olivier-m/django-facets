# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
import re
from urllib import unquote
from urlparse import urljoin, urldefrag

from django.conf import settings

CSS_URL_PATTERNS = (
    re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))"""),
    re.compile(r"""(@import\s*["']\s*(.*?)["'])"""),
)


def normalize_css_urls(content, basedir, callback=None):
    """
    Transform all URLs in a CSS content as absolute paths.
    """
    def adapt_css_url(match):
        groups = list(match.groups())
        if groups[1].find('://') != -1:
            return groups[0]

        origin, fragment = urldefrag(groups[1])
        new_url = urljoin(base_src, origin)

        if not new_url.startswith(settings.STATIC_URL):
            return groups[0]

        if callable(callback):
            new_url = callback(new_url)

        if fragment:
            new_url += "#%s" % fragment

        return 'url("%s")' % unquote(new_url)

    base_src = urljoin(settings.STATIC_URL, basedir)
    if not base_src.endswith("/"):
        base_src += "/"

    for pattern in CSS_URL_PATTERNS:
        content = pattern.sub(adapt_css_url, content)

    return content
