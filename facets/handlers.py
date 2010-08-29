# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
import os.path
import re
from subprocess import Popen, PIPE
from urlparse import urljoin

from django.conf import settings
from django.utils.importlib import import_module

class MediaHandlers(dict):
    """
    Our media handlers. A dict with lists of handlers by type.
    Instance of this class is created at the end of the file
    """
    def __init__(self, *args, **kwargs):
        super(MediaHandlers, self).__init__(*args, **kwargs)
        self.init_handlers()
    
    def init_handlers(self):
        self.clear()
        for handler_type, handlers in settings.MEDIA_CACHE_HANDLERS.items():
            self[handler_type] = []
            for handler in handlers:
                try:
                    module_name, klass = handler.rsplit('.', 1)
                    m = import_module(module_name)
                    self[handler_type].append(getattr(m, klass))
                except ImportError:
                    pass
    
    def apply_handlers(self, src, data, media_store):
        for klass in self.get(os.path.splitext(src)[1][1:], list()):
            _handler = klass(src, data, media_store)
            try:
                new_data = _handler.render()
                if new_data:
                    data = new_data
            except NotImplementedError:
                pass
        
        return data
    

class BaseHandler(object):
    """
    All custom handlers shoul inherit this class and implement a ``render``
    method.
    """
    def __init__(self, src, data, media_store):
        self.src = src
        self.data = data
        self.media_store = media_store
    
    def render(self):
        raise NotImplementedError()

class InOutHandler(BaseHandler):
    """
    A base handler for all stdin to stdout operation through an external
    command. ``cmd`` should be a tuple or a list.
    """
    cmd = None
    
    def render(self):
        if not isinstance(self.cmd, (tuple, list)) or len(self.cmd) == 0:
            raise NotImplementedError()
        
        if not self.cmd[0] or not os.path.isfile(self.cmd[0]):
            return
        
        try:
            p = Popen(self.cmd, stdin=PIPE, stdout=PIPE)
        except OSError:
            return
        else:
            res, __ = p.communicate(self.data)
            if res:
                return res
    

class CssUrls(BaseHandler):
    re_url = re.compile(r'(url\(["\']?)(.+?)(["\']?\))', re.M)
    
    def render(self):
        self.base_src = '%s/' % urljoin(settings.MEDIA_URL, os.path.dirname(self.src))
        self.base_dst = '%s/' % urljoin(settings.MEDIA_CACHE_URL, os.path.dirname(self.src))
        
        return self.re_url.sub(self.adapt_url, self.data)
    
    def adapt_url(self, match):
        groups = list(match.groups())
        if groups[1].find('://') != -1:
            return ''.join(groups)
        
        url = urljoin(self.base_src, groups[1])
        store_key = url[len(settings.MEDIA_URL):]
        
        if store_key in self.media_store.keys():
            groups[1] = urljoin(settings.MEDIA_CACHE_URL, self.media_store[store_key])
        
        return ''.join(groups)
    

class CssMin(BaseHandler):
    def render(self):
        try:
            from cssmin import cssmin
        except ImportError:
            return
        else:
            data = cssmin(self.data)
            if data:
                return data
    

class UglifyJs(InOutHandler):
    if isinstance(settings.MEDIA_CACHE_UGLIFYJS, (tuple, list)):
        cmd = settings.MEDIA_CACHE_UGLIFYJS
    else:
        cmd = (settings.MEDIA_CACHE_UGLIFYJS,)

class GoogleClosureCompiler(InOutHandler):
    cmd = settings.MEDIA_GOOGLE_COMPILER

media_handlers = MediaHandlers()