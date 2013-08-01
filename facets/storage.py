# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
import hashlib
import json
import os
import sys
from urlparse import urldefrag, urljoin

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import force_unicode, smart_str, filepath_to_uri

from facets.collections import MediaCollectionList, parse_templates


class FacetsFilesMixin(object):
    def __init__(self, *args, **kwargs):
        super(FacetsFilesMixin, self).__init__(*args, **kwargs)

        self._cache = None

    def write_media_store(self, data):
        data = json.dumps(data, indent=2)
        with open(settings.FACETS_STORE, "wb") as fp:
            fp.write(data)

    def load_media_store(self):
        with open(settings.FACETS_STORE, "rb") as fp:
            data = json.load(fp)

        return data

    @property
    def cache(self):
        if self._cache is not None:
            return self._cache

        try:
            self._cache = self.load_media_store()
        except:
            self._cache = {}

        return self._cache

    def url(self, name):
        if not settings.FACETS_ACTIVE:
            return super(FacetsFilesMixin, self).url(name)

        cached_file = self.cache.get(self.cache_key(name))
        if not cached_file:
            return super(FacetsFilesMixin, self).url(name)

        return urljoin(self.base_url, filepath_to_uri(cached_file))

    def cache_key(self, name):
        return force_unicode(urldefrag(name)[0])

    def hashed_name(self, name, content):
        # Get the MD5 hash of the file
        md5 = hashlib.md5()
        for chunk in content.chunks():
            md5.update(chunk)
        md5sum = md5.hexdigest()[:12]

        root, ext = os.path.splitext(name)
        return u"%s-%s%s" % (root, md5sum, ext)

    def post_process(self, paths, dry_run=False, **options):
        if dry_run:
            return

        # Browse for collections
        FACETS_ACTIVE = settings.FACETS_ACTIVE
        settings.FACETS_ACTIVE = False

        collection_list = MediaCollectionList()
        for _collections in parse_templates():
            if isinstance(_collections, Exception):
                msg = "ERROR: Unable to get collections - %s" % _collections
                sys.stderr.write("%s\n" % msg)
            else:
                collection_list.update(_collections)

        settings.FACETS_ACTIVE = FACETS_ACTIVE

        for collection in collection_list:
            data = collection.get_data()
            path = self.path(collection.path)

            if not self.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            with open(path, 'wb') as fp:
                fp.write(smart_str(data))
            os.chmod(path, 0755)
            sys.stdout.write("Wrote collection '%s'\n" % path)

            paths[force_unicode(collection.path)] = (
                FileSystemStorage(self.location),
                force_unicode(collection.path)
            )

        media_store = {}
        path_level = lambda name: len(name.split(os.sep))
        keys = sorted(paths.keys(), key=path_level, reverse=True)

        # First, create a cache dictionnary
        for name in keys:
            storage, path = paths[name]

            with storage.open(path) as original_file:
                media_store[self.cache_key(name)] = self.hashed_name(force_unicode(name), original_file)

        # Now, apply handlers and create cached files
        from facets.handlers import media_handlers

        for name in keys:
            storage, path = paths[name]

            # First, write file copy
            with storage.open(path) as original_file:
                content_file = ContentFile(smart_str(original_file.read()))
                saved_name = media_store[self.cache_key(name)]
                filename = self.path(saved_name)

                # Avoid creation of a new file
                if os.path.exists(filename):
                    os.unlink(filename)

                saved_name = self._save(media_store[self.cache_key(name)], content_file)

            # Call handlers
            media_handlers.apply_handlers(self, path, media_store)

            yield name, saved_name, True

        # Writing cache values
        self.write_media_store(media_store)
        sys.stdout.write("Wrote mediastore '%s'" % settings.FACETS_STORE)


class FacetsFilesStorage(FacetsFilesMixin, StaticFilesStorage):
    pass
