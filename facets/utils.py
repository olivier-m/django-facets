# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
import hashlib
import os
import shutil

from django.conf import settings
from django.utils.importlib import import_module

from facets.handlers import media_handlers

def files_checksum(*files):
    m = hashlib.md5()
    for f in files:
        fp = open(f, 'rb')
        while True:
            data = fp.read(128)
            if not data:
                break
            m.update(data)
    
    return m.hexdigest()[0:8]

def copy_file(src, dst, media_store):
    src_path = os.path.join(settings.MEDIA_ROOT, src)
    dst_path = os.path.join(settings.MEDIA_CACHE_ROOT, dst)
    dst_dir = os.path.dirname(dst_path)
    
    data = open(src_path, 'rb').read()
    
    # Applying media handlers
    data = media_handlers.apply_handlers(src, data, media_store)
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    fp = open(dst_path, 'wb')
    fp.write(data)
    fp.close
    shutil.copymode(src_path, dst_path)
    shutil.copystat(src_path, dst_path)

