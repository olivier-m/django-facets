# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
import os
import shutil
from urlparse import urljoin

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django import template

from facets import store
from facets.templatetags import mediafiles as media_tags
from facets.utils import copy_file, files_checksum

class Command(NoArgsCommand):
    help = "Generate media files for production"
    
    def handle_noargs(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        media_store = store.MediaStore()
        
        if not settings.MEDIA_CACHE_ROOT:
            raise CommandError('You should have a MEDIA_CACHE_ROOT setting.')
        
        if settings.MEDIA_CACHE_ROOT == settings.MEDIA_ROOT:
            raise CommandError('MEDIA_CACHE_ROOT should not be the same directory as MEDIA_ROOT.')
        
        root = settings.MEDIA_CACHE_ROOT
        if os.path.exists(root) and not os.path.isdir(root):
            raise CommandError('MEDIA_CACHE_ROOT "%s" is not a directory.' % root)
        
        if os.path.exists(root):
            if verbosity:
                print "Empty %s directory" % root
                shutil.rmtree(root)
        
        if verbosity:
            print "Making %s directory" % root
        os.makedirs(root)
        
        # Before generating collections we need to set MEDIA_CACHE_ACTIVE
        # to False
        setattr(settings, 'MEDIA_CACHE_ACTIVE', False)
        
        collections = self.parse_templates(options)
        
        # Copy all files in media_store
        for src, dst in media_store.items():
            copy_file(src, dst, media_store)
        
        for col in collections:
            col_file, col_url = col.make_file(media_store,
                settings.MEDIA_URL, settings.MEDIA_CACHE_ROOT)
            
            media_store[col.path] = col_url
        
        # Copy media_store representation in a python file
        fp = open(settings.MEDIA_CACHE_STORE, 'wb')
        fp.write('# -*- coding: utf-8 -*-\n')
        fp.write('media_store = %s' % repr(media_store))
        fp.close()
    
    def parse_templates(self, options):
        # Most parts of this code comes from django assets
        #
        template_dirs = []
        if 'django.template.loaders.filesystem.Loader' in settings.TEMPLATE_LOADERS:
            template_dirs.extend(settings.TEMPLATE_DIRS)
        if 'django.template.loaders.app_directories.Loader' in settings.TEMPLATE_LOADERS:
            from django.template.loaders.app_directories import app_template_dirs
            template_dirs.extend(app_template_dirs)
        
        collections = set()
        total_count = 0
        for template_dir in template_dirs:
            for directory, _ds, files in os.walk(template_dir):
                for filename in files:
                    if filename.endswith('.html'):
                        total_count += 1
                        tmpl_path = os.path.join(directory, filename)
                        collections.update(self.parse_template(options, tmpl_path))
        
        if options.get('verbosity') >= 1:
            print "Parsed %d templates, found %d valid collections." % (
                total_count, len(collections))
        return collections
    
    def parse_template(self, options, tmpl_path):
        contents = open(tmpl_path, 'rb').read()
        try:
            t = template.Template(contents)
        except template.TemplateSyntaxError, e:
            if options.get('verbosity') >= 2:
                print self.style.ERROR('\tdjango parser failed, error was: %s'%e)
            return set()
        else:
            result = set()
            def _recurse_node(node):
                # depending on whether the template tag is added to
                # builtins, or loaded via {% load %}, it will be
                # available in a different module
                if isinstance(node, media_tags.MediaCollectionNode):
                    # try to resolve this node's data; if we fail,
                    # then it depends on view data and we cannot
                    # manually rebuild it.
                    try:
                        collection = node.resolve()
                    except template.VariableDoesNotExist:
                        if options.get('verbosity') >= 2:
                            print self.style.ERROR('\tskipping asset %s, depends on runtime data.' % node.output)
                    else:
                        result.add(collection)
                # see Django #7430
                for subnode in hasattr(node, 'nodelist') and node.nodelist or []:
                    _recurse_node(subnode)
            
            for node in t:  # don't move into _recurse_node, ``Template`` has a .nodelist attribute
                _recurse_node(node)
            
            return result
    

