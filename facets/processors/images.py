# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from facets.processors.base import CommandProcessor


class OptiPngProcessor(CommandProcessor):
    match = r'\.png$'

    program = '/usr/bin/env optipng'
    command = '{program} -o7 -nc {infile}'

    def process(self):
        self.execute_cmd(infile=self.storage.path(self.path))


class AdvPngProcessor(CommandProcessor):
    match = r'\.png$'

    program = '/usr/bin/env advpng'
    command = '{program} -z -4 {infile}'

    def process(self):
        self.execute_cmd(infile=self.storage.path(self.path))


class JpegtranProcessor(CommandProcessor):
    match = r'\.jpe?g$'

    program = '/usr/bin/env jpegtran'
    command = '{program} -copy none -optimize {infile}'

    def process(self):
        self.execute_cmd(infile=self.storage.path(self.path))


class JpegoptimProcessor(CommandProcessor):
    match = r'\.jpe?g$'

    program = '/usr/bin/env jpegoptim'
    command = '{program} -q --strip-all {infile}'

    def process(self):
        self.execute_cmd(infile=self.storage.path(self.path))


class GifsicleProcessor(CommandProcessor):
    match = r'\.gif$'

    program = '/usr/bin/env gifsicle'
    command = '{program} --batch -O3 {infile}'

    def process(self):
        self.execute_cmd(infile=self.storage.path(self.path))
