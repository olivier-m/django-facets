# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from facets.processors.base import CommandProcessor, Processor, ProcessorError
from facets.processors.css import YuiCssProcessor


class JsMinProcessor(Processor):
    match = r'\.js$'

    def process(self):
        try:
            from jsmin import jsmin
        except ImportError:
            raise ProcessorError('Unable to import jsmin module.')

        self.save_contents(jsmin(self.read()))


class UglifyJsProcessor(CommandProcessor):
    match = r'\.js$'

    program = '/usr/bin/env uglifyjs'
    command = '{program} {infile} --ascii -m -c -o {outfile}'

    def process(self):
        full_path = self.storage.path(self.path)
        self.execute_cmd(infile=full_path, outfile=full_path)


class YuiJsProcessor(YuiCssProcessor):
    match = r'\.js$'


class GoogleClosureProcessor(CommandProcessor):
    match = r'\.js$'

    program = '/usr/bin/env java -jar /path/to/compiler.jar'
    command = '{program} {infile}'

    def process(self):
        contents = self.execute_cmd(infile=self.storage.path(self.path))
        self.save_contents(contents)
