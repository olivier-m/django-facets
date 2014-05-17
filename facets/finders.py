# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.contrib.staticfiles.finders import BaseStorageFinder, get_finders
from django.contrib.staticfiles.storage import StaticFilesStorage

from facets.conf import settings
from facets.handlers import default_handlers


def find_in_base_finders(path, all=False):
    """
    Find a file in all base finders
    """
    matches = []
    for finder in get_finders():
        if isinstance(finder, FacetsFinder):
            continue

        result = finder.find(path, all=all)
        if not all and result:
            return result
        if not isinstance(result, (list, tuple)):
            result = [result]
        matches.extend(result)
    if matches:
        return matches
    # No match.
    return all and [] or None


class FacetsFinder(BaseStorageFinder):
    storage = StaticFilesStorage

    def find(self, path, all=False):
        if settings.FACETS_ENABLED:
            return []  # Production

        original = find_in_base_finders(path, False)
        if not original:
            return []

        compiler = default_handlers.get_compiler(original, self.storage, path)
        if compiler is None:
            return all and [original] or original

        if not compiler.should_compile():
            return self.storage.path(compiler.new_name)

        full_path = compiler.storage.path(compiler.compile())
        return all and [full_path] or full_path

    def list(self, ignore_patterns):
        return []
