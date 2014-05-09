# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
import hashlib
import os
import sys
from urlparse import urldefrag, urljoin


from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.cache import get_cache, InvalidCacheBackendError, cache as default_cache
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from django.utils.encoding import force_unicode, smart_str, filepath_to_uri

from facets.collections import MediaCollectionList, parse_templates
from facets.utils import normalize_css_urls


class MediaStore(object):
    def __init__(self):
        try:
            self.cache = get_cache('facets')
        except InvalidCacheBackendError:
            self.cache = default_cache

        self.files = self.cache.get('facets:files', {})

    def save(self):
        self.cache.set('facets:files', self.files)


class FacetsFilesMixin(object):
    def __init__(self, *args, **kwargs):
        super(FacetsFilesMixin, self).__init__(*args, **kwargs)
        self.cache = MediaStore()

    def url(self, name):
        if not settings.FACETS_ACTIVE:
            return super(FacetsFilesMixin, self).url(name)

        cached_file = self.cache.files.get(self.cache_key(name))
        if not cached_file:
            return super(FacetsFilesMixin, self).url(name)

        return urljoin(self.base_url, filepath_to_uri(cached_file))

    def cache_key(self, name):
        return force_unicode(urldefrag(name)[0])

    def hashed_name(self, name, content):
        # Get the MD5 hash of the file
        md5 = hashlib.md5()
        if hasattr(content, 'chunks'):
            for chunk in content.chunks():
                md5.update(chunk)
        else:
            md5.update(content)

        md5sum = md5.hexdigest()[:12]

        root, ext = os.path.splitext(name)
        return u"%s-%s%s" % (root, md5sum, ext)

    def get_linked_files(self, paths):
        """
        Returns a dictionnary of paths linked in CSS.
        """
        files = dict([(k, v) for k, v in paths.items() if os.path.splitext(k)[1] == '.css'])

        result = {}

        def add_to_result(key_name, url):
            if url.startswith(settings.STATIC_URL):
                url = url[len(settings.STATIC_URL):]

                if not url in result:
                    result[url] = [key_name]
                elif key_name not in result[url]:
                    result[url].append(key_name)

            return url

        for name in files.keys():
            storage, path = files[name]
            key_name = self.cache_key(name)
            with storage.open(path) as fp:
                data = force_unicode(fp.read())
                normalize_css_urls(data, os.path.dirname(path),
                    lambda x: add_to_result(key_name, x)
                )

        return result

    def process_file(self, name, storage, path, force=False):
        with storage.open(path) as original_file:
            # Compute key and hash
            key_name = self.cache_key(name)
            hashed_name = self.hashed_name(force_unicode(name), original_file)

            if hasattr(original_file, 'seek'):
                original_file.seek(0)

            hashed_file_exists = self.exists(hashed_name)
            processed = False

            if force or not hashed_file_exists:
                # Copy file
                processed = True
                self.exists(hashed_name) and self.delete(hashed_name)
                self._save(hashed_name, original_file)

            # Check for an old hashed_name to remove
            if key_name in self.cache.files and self.cache.files[key_name] != hashed_name:
                self.exists(self.cache.files[key_name]) and self.delete(self.cache.files[key_name])

            return key_name, hashed_name, processed

    def apply_handlers(self, key_name, media_store):
        from facets.handlers import media_handlers
        success_msg = "Applied handler {0} on '{1}'\n"
        error_msg = 'ERROR: Unable to execute handler {0} on {1}. Error was: {2}\n'

        for path, handler, error in media_handlers.apply_handlers(self, key_name, media_store):
            if error is None:
                sys.stdout.write(success_msg.format(repr(handler.__class__), path))
            else:
                sys.stderr.write(error_msg.format(repr(handler.__class__), path, str(error)))

    def post_process(self, paths, dry_run=False, **options):
        # Dry-run, stop it now
        if dry_run:
            return

        # Stored file list
        media_store = {}

        # First, create dependencies tree on CSS files
        dependencies = self.get_linked_files(paths)
        processed_list = {}

        # Iterate on files and process them if not already cached
        for name in sorted(paths.keys()):
            storage, path = paths[name]
            key_name, hashed_name, processed = self.process_file(name, storage, path)
            media_store[key_name] = hashed_name

            if processed:
                processed_list[key_name] = hashed_name

            yield name, hashed_name, processed

        # Iterate on processed files in case we need to update linked files
        keys = processed_list.keys()
        for key_name in keys:
            if key_name not in dependencies:
                # File has no dependency
                continue

            for _name in dependencies[key_name]:
                if _name in keys:
                    # Dependency has already been processed
                    continue

                # Dependency forced update
                storage, path = paths[_name]
                key_name, hashed_name, processed = self.process_file(_name, storage, path, True)
                media_store[key_name] = hashed_name

                if processed:
                    processed_list[key_name] = hashed_name

                yield _name, hashed_name, processed

        # Get collection list (to be processed later)
        with override_settings(FACETS_ACTIVE=False):
            collection_list = MediaCollectionList()
            for _collections in parse_templates():
                if isinstance(_collections, Exception):
                    raise _collections
                else:
                    collection_list.update(_collections)

        # Apply handlers on processed files
        for key_name in processed_list.keys():
            self.apply_handlers(key_name, media_store)

        # Process collections
        for collection in collection_list:
            if collection.path in paths:
                raise ValueError('(Collection) File {0} already exists.'.format(collection.path))

            # Get original media keys
            media_keys = [x[len(self.base_url):] for x in collection.media]

            # Is there processed files in collection?
            has_changes = len(set(processed_list.keys()) & set(media_keys)) > 1

            key_name = self.cache_key(collection.path)
            hashed_name = self.cache.files.get(key_name)

            files_exist = self.exists(collection.path) and hashed_name and self.exists(hashed_name)

            # If there are no changes and files exist, stop now
            if not has_changes and files_exist:
                media_store[key_name] = hashed_name
                continue

            # Create "unprocessed" collection file
            path = self.path(collection.path)
            if not self.exists(os.path.dirname(collection.path)):
                os.path.makedirs(os.path.dirname(path))

            with open(path, 'wb') as fp:
                fp.write(smart_str(collection.get_data()))
            sys.stdout.write("Wrote collection '{0}'.\n".format(collection.path))

            # Process file and apply handlers
            key_name, hashed_name, processed = self.process_file(
                collection.path,
                FileSystemStorage(self.location),
                collection.path,
                True
            )

            media_store[key_name] = hashed_name
            yield key_name, hashed_name, processed

            self.apply_handlers(key_name, media_store)

        # Saved file list
        self.cache.files = media_store
        self.cache.save()


class FacetsFilesStorage(FacetsFilesMixin, StaticFilesStorage):
    pass
