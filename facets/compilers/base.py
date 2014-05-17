# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from datetime import datetime
import os.path

from django.core.files.base import ContentFile
from django.utils.encoding import smart_str

from facets.utils import CommandHandlerMixin


class CompilerError(Exception):
    pass


class Compiler(object):
    extension = None
    new_name = '{base}.{extension}'
    remove_original = True

    def __init__(self, original, storage, path, **options):
        self.original = original
        self.storage = storage
        self.path = path
        self.__dict__.update(options)

        base, extension = os.path.splitext(self.path)
        self.new_name = self.new_name.format(base=base, extension=extension[1:])

    def compile(self):
        """
        Compilation function. This function should save file to destination and return
        the new relative path of saved file.
        """
        raise NotImplementedError()

    def save_contents(self, contents):
        out = ContentFile(smart_str(contents))
        self.storage.exists(self.new_name) and self.storage.delete(self.new_name)
        self.storage.save(self.new_name, out)

    def get_dependencies(self):
        return set()

    def should_compile(self):
        if not self.storage.exists(self.new_name):
            return True

        otime = self.storage.modified_time(self.new_name)
        mtime = datetime.fromtimestamp(os.path.getmtime(self.original))
        if mtime > otime:
            return True

        for path in self.get_dependencies():
            if not os.path.exists(path):
                return True
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime > otime:
                return True

        return False


class CommandCompiler(Compiler, CommandHandlerMixin):
    pass
