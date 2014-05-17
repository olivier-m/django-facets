# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from facets.compilers.base import CommandCompiler


class CoffeScriptCompiler(CommandCompiler):
    extensions = ('coffee',)
    new_name = '{base}.js'

    program = '/usr/bin/env coffee'
    command = '{program} -c --print {infile}'

    def compile(self):
        contents = self.execute_cmd(infile=self.original)
        self.save_contents(contents)

        return self.new_name


class LiveScriptCompiler(CommandCompiler):
    extensions = ('ls',)
    new_name = '{base}.js'

    program = '/usr/bin/env lsc'
    command = '{program} -c --print {infile}'

    def compile(self):
        contents = self.execute_cmd(infile=self.original)
        self.save_contents(contents)

        return self.new_name


class DartCompiler(CommandCompiler):
    extensions = ('dart',)
    new_name = '{base}.js'

    program = '/usr/bin/env dart2js'
    command = '{program} -o {outfile} {infile}'

    def compile(self):
        self.execute_cmd(infile=self.original, outfile=self.storage.path(self.new_name))
        return self.new_name
