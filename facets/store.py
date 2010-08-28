# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
import imp
import os

from django.conf import settings

from facets.utils import files_checksum

class MediaStore(dict):
    def __init__(self, *args, **kwargs):
        super(MediaStore, self).__init__(*args, **kwargs)
        self.__root = None
        if os.path.isdir(settings.MEDIA_ROOT):
            self.__root = os.path.realpath(settings.MEDIA_ROOT)
        
        self.rebuild()
    
    def __media_version(self, path):
        media_path = path[len(self.__root)+1:]
        splited = os.path.splitext(media_path)
        version = files_checksum(path)
        return media_path, '%s-%s%s' % (splited[0], version, splited[1])
    
    def rebuild(self):
        if not self.__root:
            return
        
        self.clear()
        
        for dirpath, dirnames, filenames in os.walk(self.__root):
            for path in filenames:
                media_path, version = self.__media_version(os.path.join(dirpath, path))
                self[media_path] = version
    

try:
    m = imp.load_source('cache_store', settings.MEDIA_CACHE_STORE)
    media_store = getattr(m, 'media_store', {})
except (IOError, ImportError, TypeError):
    media_store = {}
