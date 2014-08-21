# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from gzip import GzipFile

from facets.processors.base import Processor, ProcessorError


class GZipProcessor(Processor):
    match = r'\.(htm|html|js|css|txt|eot|ttf|svg)'
    priority = 1000

    compresslevel = 5

    def process(self):
        outfile = '{0}.gz'.format(self.path)

        with self.storage.open(self.path, 'rb') as f_in:
            try:
                f_out = GzipFile(
                    self.storage.path(outfile), 'wb',
                    compresslevel=self.compresslevel
                )
            except Exception as e:
                raise ProcessorError(str(e))

            [f_out.write(chunk) for chunk in f_in.chunks()]
            f_out.close()

        return outfile
