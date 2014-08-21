# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path

from django.conf import settings
from django.utils.encoding import smart_str, force_bytes

from facets.compilers.base import CommandCompiler, Compiler, CompilerError
from facets.finders import get_base_finders_locations


class LessCompiler(CommandCompiler):
    extensions = ('less',)
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    program = '/usr/bin/env lessc'
    command = '{program} {options} {infile} {outfile}'

    def compile(self):
        outfile = self.storage.path(self.new_name)

        locations = list(get_base_finders_locations())
        options = (
            '--include-path={0}'.format(':'.join(reversed(locations))),
            '--global-var=\'STATIC_URL="{0}"\''.format(settings.STATIC_URL)
        )

        self.execute_cmd(infile=self.original, outfile=outfile, options=' '.join(options))
        return self.new_name


class SasscCompiler(CommandCompiler):
    extensions = ('scss', 'sass')
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    program = '/usr/bin/env sassc'
    command = '{program} {options}'

    def compile(self):
        with open(self.original, 'r') as fp:
            contents = smart_str('$STATIC_URL: "{0}";\n\n{1}'.format(
                settings.STATIC_URL, fp.read())
            )

        locations = list(get_base_finders_locations())
        locations.append(os.path.dirname(self.original))
        options = '-I {0}'.format(':'.join(reversed(locations)))

        contents = self.execute_cmd(data=contents, options=options)
        self.save_contents(contents)

        return self.new_name


class LibSassCompiler(Compiler):
    extensions = ('scss', 'sass')
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    def compile(self):
        try:
            import sass
        except ImportError:
            raise CompilerError('Unable to import sass module.')

        with open(self.original, 'r') as fp:
            contents = smart_str('$STATIC_URL: "{0}";\n\n{1}'.format(
                settings.STATIC_URL, fp.read())
            )

        locations = list(get_base_finders_locations())
        locations.append(os.path.dirname(self.original))

        contents = sass.compile_string(
            force_bytes(contents),
            include_paths=force_bytes(':'.join(reversed(locations)))
        )

        self.save_contents(contents)

        return self.new_name


class StylusCompiler(CommandCompiler):
    extensions = ('styl',)
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    program = '/usr/bin/env stylus'
    command = '{program} -p {options}'

    def compile(self):
        with open(self.original, 'r') as fp:
            contents = 'STATIC_URL = \'{0}\'\n\n{1}'.format(settings.STATIC_URL, fp.read())

        locations = list(get_base_finders_locations())
        locations.insert(0, os.path.dirname(self.original))

        options = ' '.join(['-I {0}'.format(x) for x in locations])

        contents = self.execute_cmd(data=contents, options=options)
        self.save_contents(contents)

        return self.new_name
