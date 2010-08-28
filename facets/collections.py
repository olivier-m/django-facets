# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import hashlib
import os.path
from urlparse import urljoin

import html5lib
from html5lib import treebuilders

from facets.utils import files_checksum

def _attr_data(data):
    data = data.replace("&", "&amp;").replace("<", "&lt;")
    data = data.replace("\"", "&quot;").replace(">", "&gt;")
    return data

class CollectionException(Exception):
    pass

class MediaCollection(object):
    def __init__(self, data, path):
        parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
        node = parser.parseFragment(data)
        self.node = node
        self.path = path
        self.init_collection()
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and hash(self) == hash(other)
    
    def __hash__(self):
        m = hashlib.md5()
        [m.update(x) for x in self.media]
        m.update(self.path)
        return int(m.hexdigest(), 16)
    
    def clear(self):
        self.type = None
        self.attrs = {}
        self.media = []
    
    def init_collection(self):
        self.clear()
        for n in self.node.childNodes:
            if n.nodeType == n.TEXT_NODE:
                continue
            if n.nodeType != n.ELEMENT_NODE:
                raise CollectionException('Collection contains non element nodes.')
            
            name = n.nodeName.lower()
            if self.type and self.type != name:
                raise CollectionException('Collection contains elements of type %s only.' % self.type)
            
            self.type = name
            
            if name == 'link':
                self.set_prop_link(n)
            elif name == 'script':
                self.set_prop_script(n)
    
    def attr_value(self, node, name, default=None):
        attr = node.attributes.get(name)
        if attr is None:
            return default
        
        return attr.value
    
    def set_prop_link(self, node):
        rel = self.attr_value(node, 'rel')
        href = self.attr_value(node, 'href')
        ctype = self.attr_value(node, 'type', 'text/css')
        media = self.attr_value(node, 'media', 'screen')
        
        if self.attrs.get('rel') not in (None, rel):
            raise CollectionException('All rel attributes should be the same in collection.')
        if self.attrs.get('type') not in (None, ctype):
            raise CollectionException('All type attributes should be the same in collection.')
        if self.attrs.get('media') not in (None, media):
            raise CollectionException('All media attributes should be the same in collection.')
        
        self.attrs.update({
            'rel': rel, 'type': ctype, 'media': media
        })
        
        self.media.append(href)
    
    def set_prop_script(self, node):
        ctype = self.attr_value(node, 'type', 'text/javascript')
        src = self.attr_value(node, 'src')
        
        if src is None:
            raise CollectionException('No src attribute in collection script tag.')
        if self.attrs.get('type') not in (None, ctype):
            raise CollectionException('All type attributes should be the same in collection.') 
        
        self.attrs.update({
            'type': ctype,
        })
        
        self.media.append(src)
    
    def get_html(self, base_url):
        if self.type == 'link':
            return self.get_html_link(base_url)
        elif self.type == 'script':
            return self.get_html_script(base_url)
    
    def get_html_link(self, base_url):
        attrs = dict(self.attrs)
        attrs['href'] = urljoin(base_url, self.path)
        tag = '<link %s />'
        return tag % ' '.join(
            ['%s="%s"' % (k, _attr_data(v)) for k,v in attrs.items()]
        )
    
    def get_html_script(self, base_url):
        attrs = dict(self.attrs)
        attrs['src'] = urljoin(base_url, self.path)
        tag = '<script %s></script>'
        return tag % ' '.join(
            ['%s="%s"' % (k, _attr_data(v)) for k,v in attrs.items()]
        )
    
    def make_file(self, media_store, media_url, cache_root):
        """
        Creates a collection file and return its destination path and url
        """
        files = [os.path.join(cache_root, media_store[y]) for y in
            [x[len(media_url):] for x in self.media]
        ]
        
        out = StringIO()
        for f in files:
            fp = open(f, 'rb')
            out.write(fp.read())
            out.write('\n')
            fp.close()
        
        outurl = ('-%s' % files_checksum(*files)).join(
            os.path.splitext(self.path)
        )
        outfile = os.path.join(cache_root, outurl)
        
        fp = open(outfile, 'wb')
        fp.write(out.getvalue())
        fp.close()
        
        return outfile, outurl
    
