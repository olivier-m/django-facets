# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the BSD license.
# See the LICENSE for more information.
from setuptools import setup, find_packages

version = '0.2'
packages = ['facets'] + ['facets.%s' % x for x in find_packages('facets',)]

setup(
    name='facets',
    version=version,
    description='Media collections manager for Django.',
    author='Olivier Meunier',
    author_email='om@neokraft.net',
    url='https://github.com/olivier-m/django-facets',
    packages=packages,
    classifiers=[
        'Development Status :: %s' % version,
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
