# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from distutils.spawn import find_executable
from gzip import GzipFile
import os
import re
from subprocess import Popen, PIPE
import sys
from urlparse import urljoin


from django.conf import settings
from django.utils.encoding import force_unicode, smart_str
from django.utils.importlib import import_module

from facets.utils import normalize_css_urls


class MediaHandlers(object):
    """
    Our media handlers. Contains a dict with lists of handlers by type.
    Instance of this class is created at the end of the file
    """
    def __init__(self):
        self._handlers = []
        for handler in settings.FACETS_HANDLERS:
            options = {}
            if isinstance(handler, (tuple, list)):
                handler, options = handler

            try:
                module_name, klass = handler.rsplit('.', 1)
                m = import_module(module_name)
                self._handlers.append((getattr(m, klass), options))
            except ImportError:
                pass

    def apply_handlers(self, storage, path, media_store):
        for klass, options in self._handlers:
            if klass.match is None or not re.search(klass.match, path):
                continue

            try:
                handler = klass(storage, path, media_store, options)
                handler.render()

                msg = "Applied handler %s on '%s'" % (repr(klass), media_store[path])
                sys.stdout.write("%s\n" % msg)
            except HandlerError, e:
                msg = "WARNING: Unable to execute handler %s on %s. Error was: %s" % \
                        (repr(klass), path, str(e))

                sys.stderr.write("%s\n" % msg)
            except BaseException, e:
                msg = "ERROR: Unable to execute handler %s on %s. Error was: %s" % \
                        (repr(klass), path, str(e))

                sys.stderr.write("%s\n" % msg)
                raise


class HandlerError(Exception):
    pass


class BaseHandler(object):
    """
    All custom handlers shoul inherit this class and implement a ``render``
    method.
    """
    match = None

    def __init__(self, storage, path, media_store, options):
        self.storage = storage
        self.origin = path
        self.path = media_store[self.origin]
        self.media_store = media_store
        self.options = options

    def render(self):
        raise HandlerError("Handler does not implement renderer.")

    def warn(self, msg):
        pass

    def read(self):
        with self.storage.open(self.path, 'rb') as fp:
            return force_unicode(fp.read())

    def save(self, data):
        with self.storage.open(self.path, 'wb') as fp:
            fp.write(smart_str(data))

    def copy_mode(self, from_file=None, to_file=None):
        from_file = from_file or self.storage.path(self.origin)
        to_file = to_file or self.storage.path(self.path)

        os.chmod(to_file, os.stat(from_file).st_mode)


class CommandHandler(BaseHandler):
    """
    A base handler for all operation through an external command. Command should take the
    file path as a last argument and modify it in place.
    """
    default_cmd = None

    def get_command(self):
        cmd = list(self.options.get('COMMAND', self.default_cmd))

        if not cmd:
            raise HandlerError("You should provide a COMMAND option.")

        if not isinstance(cmd, (tuple, list)):
            raise HandlerError("COMMAND option should be a tuple of arguments.")

        if not cmd[0] or not os.path.isfile(cmd[0]):
            cmd[0] = find_executable(cmd[0])
            if not cmd[0]:
                raise HandlerError('Command "%s" not found.' % cmd[0])

        return cmd

    def get_full_command(self):
        cmd = self.get_command()
        cmd.append(self.storage.path(self.path))

        return cmd

    def execute(self, cmd, data=None):
        try:
            p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except OSError, e:
            raise HandlerError("OSError on command: %s" % str(e))
        else:
            out, err = p.communicate(data)
            if p.returncode != 0:
                raise HandlerError("Command error: %s" % err)

            return out

    def render(self, data=None):
        cmd = self.get_full_command()
        res = self.execute(cmd, data)
        self.copy_mode()
        return res


class InOutHandler(CommandHandler):
    """
    A base handler for all stdin to stdout operation through an external
    command. ``cmd`` should be a tuple or a list.
    """
    def get_full_command(self):
        return self.get_command()

    def render(self):
        data = super(InOutHandler, self).render(self.read())
        self.save(data)


class YuiHandler(CommandHandler):
    """
    A Yahoo UI compressor base handler.
    """
    def render(self, data=None):
        data = super(YuiHandler, self).render()
        self.save(data)


class CssUrls(BaseHandler):
    match = r"\.css$"

    def find_media(self, url):
        store_key = force_unicode(url[len(settings.STATIC_URL):])
        if store_key in self.media_store:
            return urljoin(settings.STATIC_URL, self.media_store[store_key])

        return url

    def render(self):
        data = self.read()
        data = normalize_css_urls(data, os.path.dirname(self.origin), self.find_media)
        self.save(data)


class CssMin(BaseHandler):
    match = r"\.css$"

    def render(self):
        try:
            from cssmin import cssmin
        except ImportError:
            raise HandlerError("Unable to import cssmin module.")

        data = cssmin(self.read())
        if data:
            self.save(data)


class JsMin(BaseHandler):
    match = r"\.js$"

    def render(self):
        try:
            from jsmin import jsmin
        except ImportError:
            raise HandlerError("Unable to import jsmin module.")

        data = jsmin(self.read())
        if data:
            self.save(data)


class UglifyJs(CommandHandler):
    match = r"\.js$"

    def get_command(self):
        cmd = super(UglifyJs, self).get_command()

        cmd.extend(['-o', self.storage.path(self.path)])
        return cmd


class GoogleClosureCompiler(CommandHandler):
    match = r"\.js$"

    def get_full_command(self):
        cmd = self.get_command()
        if not "'--warning_level" in cmd:
            cmd.extend(["--warning_level", "QUIET"])

        cmd.extend(["--js", self.storage.path(self.path)])

        return cmd

    def render(self, data=None):
        data = super(GoogleClosureCompiler, self).render()
        self.save(data)


class YuiJs(YuiHandler):
    match = r"\.js$"


class YuiCss(YuiHandler):
    match = r"\.css$"


class OptiPNG(CommandHandler):
    match = r"\.png$"

    default_cmd = ["/usr/bin/env", "optipng", "-o7", "-nc"]


class AdvPNG(CommandHandler):
    match = r"\.png$"

    default_cmd = ["/usr/bin/env", "advpng", "-z", "-4"]


class Jpegtran(CommandHandler):
    match = r"\.jpe?g$"

    default_cmd = ["/usr/bin/env", "jpegtran", "-copy", "none", "-optimize"]

    def render(self):
        data = super(Jpegtran, self).render()
        self.save(data)


class Jpegoptim(CommandHandler):
    match = r"\.jpe?g$"

    default_cmd = ["/usr/bin/env", "jpegoptim"]


class GZip(BaseHandler):
    match = r"\.(htm|html|js|css|txt|eot|ttf|woff)"

    def render(self):
        filename = "%s.gz" % self.storage.path(self.path)
        with open(self.storage.path(self.path)) as f_in:
            try:
                f_out = GzipFile(filename, "wb", compresslevel=self.options.get('LEVEL', 5))
            except Exception, e:
                raise HandlerError(str(e))

            [f_out.write(x) for x in f_in]
            f_out.close()

        # apply same mode as source file
        self.copy_mode(to_file=filename)


media_handlers = MediaHandlers()
