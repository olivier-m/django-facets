# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import hashlib
import os.path
import sys
from urlparse import urldefrag, urljoin

from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.base import ContentFile
from django.test.utils import override_settings
from django.utils.encoding import force_str, smart_str, filepath_to_uri

from facets.cache import cache
from facets.collections import MediaCollectionList, parse_templates
from facets.conf import settings
from facets.handlers import default_handlers
from facets.processors.base import ProcessorError
from facets.utils import CommandError, CssDependencies


class FacetsFilesMixin(object):
    def __init__(self, *args, **kwargs):
        super(FacetsFilesMixin, self).__init__(*args, **kwargs)
        self._file_cache = None

    @property
    def file_cache(self):
        if self._file_cache is None:
            self._file_cache = cache.get('facets:files', {})

        return self._file_cache

    @file_cache.setter
    def file_cache(self, value):
        self._file_cache = value
        cache.set('facets:files', value)

    def url(self, name, use_cache=True):
        if not settings.FACETS_ENABLED:
            return super(FacetsFilesMixin, self).url(name)

        # Is file compilable? then get generated name
        compiler = default_handlers.get_compiler(None, self, name)
        if compiler:
            name = compiler.new_name

        # Is file in cache?
        cached_file = use_cache and self.file_cache.get(self.cache_key(name)) or None
        if not cached_file:
            return super(FacetsFilesMixin, self).url(name)

        return urljoin(self.base_url, filepath_to_uri(cached_file))

    def cache_key(self, path):
        return force_str(urldefrag(path)[0])

    def hashed_name(self, path, content):
        # Get the MD5 hash of the file
        md5 = hashlib.md5()
        if hasattr(content, 'chunks'):
            for chunk in content.chunks():
                md5.update(chunk)
        else:
            md5.update(content)

        md5sum = md5.hexdigest()[:12]

        root, ext = os.path.splitext(path)
        return u"%s-%s%s" % (root, md5sum, ext)

    def get_linked_files(self, paths):
        """
        Returns a dictionnary of paths linked in CSS.
        """
        files = dict([(k, v) for k, v in paths.items() if os.path.splitext(k)[1] == '.css'])

        result = {}
        n = CssDependencies()
        for prefixed_path, (storage, path) in files.items():
            key_name = self.cache_key(path)
            with storage.open(path, 'rb') as fp:
                n.normalize(force_str(fp.read()), os.path.dirname(path), key_name)
                result = n.dependencies

        return result

    def copy_file(self, storage, path, force=False):
        with storage.open(path) as original_file:
            # Compute key and hash
            key_name = self.cache_key(path)
            hashed_name = self.hashed_name(force_str(path), original_file)

            if hasattr(original_file, 'seek'):
                original_file.seek(0)

            processed = False
            if force or not self.exists(hashed_name):
                # Copy file
                processed = True
                self.exists(hashed_name) and self.delete(hashed_name)
                self.save(hashed_name, original_file)

            # Check for an old hashed_name to remove
            if key_name in self.file_cache and self.file_cache[key_name] != hashed_name:
                self.exists(self.file_cache[key_name]) and self.delete(self.file_cache[key_name])

            return key_name, hashed_name, processed

    def apply_processors(self, media_store, key_name):
        success_msg = "Applied processor '{0}' on '{1}'\n"
        error_msg = 'ERROR: Unable to execute processor {0} on {1}. Error was: {2}\n'

        for processor in default_handlers.get_processors(media_store, self, media_store[key_name]):
            try:
                new_path = processor.process()
                sys.stdout.write(success_msg.format(processor, new_path or processor.path))
            except (CommandError, ProcessorError) as error:
                sys.stderr.write(error_msg.format(processor, processor.path, str(error)))

    def post_process(self, paths, dry_run=False, **options):
        # Dry-run, stop it now
        if dry_run:
            return

        #
        # Compile files
        #
        for prefixed_path, (storage, path) in paths.items():
            compiler = default_handlers.get_compiler(storage.path(path), self, path)

            if compiler is None:
                continue

            if compiler.should_compile():
                compiler.compile()
                yield path, compiler.new_name, True

            # Add this new file to paths
            if getattr(self, 'prefix', None):
                new_prefixed = os.path.join(self.prefix, compiler.new_name)
            else:
                new_prefixed = compiler.new_name

            paths[new_prefixed] = (self, compiler.new_name)

            # Remove original file when needed
            if compiler.remove_original:
                self.delete(path)
                del paths[prefixed_path]
                sys.stdout.write("Deleting '{0}'\n".format(path))

        #
        # Post process
        #
        media_store = self.file_cache
        processed_list = {}

        # First, create dependencies tree on CSS files
        dependencies = self.get_linked_files(paths)

        # Iterate on files and process them if not already cached
        for prefixed_path in sorted(paths.keys()):
            storage, path = paths[prefixed_path]
            key_name, hashed_name, processed = self.copy_file(storage, path)
            media_store[key_name] = hashed_name

            if processed:
                processed_list[key_name] = hashed_name

            yield path, hashed_name, processed

        # Iterate on processed files in case we need to update linked files
        keys = processed_list.keys()
        for key_name in keys:
            if key_name not in dependencies:
                # File has no dependencies
                continue

            for _name in dependencies[key_name]:
                if _name in keys:
                    # Dependency has already been processed
                    continue

                # Dependency forced update
                storage, path = paths[_name]
                key_name, hashed_name, processed = self.copy_file(storage, path, True)
                media_store[key_name] = hashed_name

                if processed:
                    processed_list[key_name] = hashed_name

                yield _name, hashed_name, processed

        # Get collection list (to be processed later)
        with override_settings(FACETS_ENABLED=False):
            collection_list = MediaCollectionList()
            for _collections in parse_templates():
                if isinstance(_collections, Exception):
                    raise _collections
                else:
                    collection_list.update(_collections)

        # Apply processors on processed files
        for key_name in processed_list.keys():
            self.apply_processors(media_store, key_name)

        for collection in collection_list:
            if collection.path in [x[1] for x in paths.values()]:
                raise ValueError('(Collection) File {0} already exists.'.format(collection.path))

            # Get original media keys
            media_keys = []
            for url in collection.media:
                name = url[len(self.base_url):]

                # Has been compiled?
                compiler = default_handlers.get_compiler(None, self, name)
                if compiler is not None:
                    name = compiler.new_name

                media_keys.append(name)

            # Is there processed files in collection?
            has_changes = len(set(processed_list.keys()) & set(media_keys)) > 0

            key_name = self.cache_key(collection.path)
            hashed_name = self.file_cache.get(key_name)

            file_exists = self.exists(collection.path) \
                and hashed_name is not None \
                and self.exists(hashed_name)

            if not has_changes and file_exists:
                media_store[key_name] = hashed_name
                continue

            # Fix collection media list (get compiled named)
            collection.media = [self.url(x, False) for x in media_keys]
            contents = ContentFile(smart_str(collection.get_data()))

            # Create "unprocessed" collection file
            self.exists(collection.path) and self.delete(collection.path)
            self.save(collection.path, contents)
            sys.stdout.write("Wrote collection '{0}'\n".format(collection.path))

            # Process file and apply handlers
            key_name, hashed_name, processed = self.copy_file(self, collection.path, True)

            media_store[key_name] = hashed_name
            yield key_name, hashed_name, processed

            self.apply_processors(media_store, key_name)

        # Save file cache
        self.file_cache = media_store


class FacetsFilesStorage(FacetsFilesMixin, StaticFilesStorage):
    pass
