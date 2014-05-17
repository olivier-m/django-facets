# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path
import re

from django.utils.functional import LazyObject
from django.utils.importlib import import_module

from facets.conf import settings
from facets.compilers.base import Compiler
from facets.processors.base import Processor


class HandlerList(object):
    def __init__(self, modules):
        self.compilers = {}
        self.processors = []

        for name in modules:
            options = {}
            if isinstance(name, (tuple, list)):
                name, options = name

            try:
                module_name, class_name = name.rsplit('.', 1)
                m = import_module(module_name)
                klass = getattr(m, class_name)

                if issubclass(klass, Compiler) and klass.extensions is not None:
                    for ext in klass.extensions:
                        self.compilers[ext] = (klass, options)
                elif issubclass(klass, Processor) and klass.match is not None:
                    self.processors.append((klass, options))
            except (ImportError, AttributeError):
                raise  # Do something with it?

    def get_compiler(self, original, storage, path):
        base, ext = os.path.splitext(path)
        if ext and ext[1:] in self.compilers:
            klass, options = self.compilers[ext[1:]]
            return klass(original, storage, path, **options)

        return None

    def get_processors(self, media_store, storage, path):
        processors = []
        for klass, options in self.processors:
            if re.search(klass.match, path):
                processors.append(klass(media_store, storage, path, **options))

        return sorted(processors, key=lambda p: p.priority)


class DefaultHandlers(LazyObject):
    def _setup(self):
        self._wrapped = HandlerList(settings.FACETS_HANDLERS)

default_handlers = DefaultHandlers()
