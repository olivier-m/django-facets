# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import os.path

from django.utils.encoding import smart_str

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
        options = '--include-path={0}'.format(':'.join(reversed(locations)))

        self.execute_cmd(infile=self.original, outfile=outfile, options=options)
        return self.new_name


class SasscCompiler(CommandCompiler):
    extensions = ('scss', 'sass')
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    program = '/usr/bin/env sassc'
    command = '{program} {options} {infile}'

    def compile(self):
        locations = list(get_base_finders_locations())
        options = '-I {0}'.format(':'.join(reversed(locations)))

        contents = self.execute_cmd(infile=self.original, options=options)
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
            contents = fp.read()

        locations = list(get_base_finders_locations())
        locations.append(os.path.dirname(self.original))

        contents = sass.compile_string(contents,
            include_paths=smart_str(':'.join(reversed(locations)))
        )

        self.save_contents(contents)

        return self.new_name


class StylusCompiler(CommandCompiler):
    extensions = ('styl',)
    check_extensions = ('.css',) + extensions
    new_name = '{base}.css'

    program = '/usr/bin/env stylus'
    command = '{program} -p {options} {infile}'

    def compile(self):
        locations = list(get_base_finders_locations())
        locations.insert(0, os.path.dirname(self.original))

        options = ' '.join(['-I {0}'.format(x) for x in locations])

        contents = self.execute_cmd(infile=self.original, options=options)
        self.save_contents(contents)

        return self.new_name
