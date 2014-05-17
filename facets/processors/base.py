# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.core.files.base import ContentFile
from django.utils.encoding import force_unicode, smart_str

from facets.utils import CommandHandlerMixin


class ProcessorError(Exception):
    pass


class Processor(object):
    match = None

    def __init__(self, media_store, storage, path, **options):
        self.media_store = media_store
        self.storage = storage
        self.path = path
        self.__dict__.update(**options)

    def __unicode__(self):
        return '{0}.{1}'.format(self.__class__.__module__, self.__class__.__name__)

    def __str__(self):
        return b'%s' % self.__unicode__()

    def read(self):
        with self.storage.open(self.path, 'rb') as fp:
            return force_unicode(fp.read())

    def save_contents(self, contents):
        out = ContentFile(smart_str(contents))
        self.storage.exists(self.path) and self.storage.delete(self.path)
        self.storage._save(self.path, out)

    def process(self):
        """
        Process function. This function should save file to destination and return
        the relative path of saved file (or None if not changed).
        """
        raise NotImplementedError()


class CommandProcessor(Processor, CommandHandlerMixin):
    pass
