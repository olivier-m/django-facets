# -*- coding: utf-8 -*-
#
# This file is part of Django facets released under the MIT license.
# See the LICENSE for more information.
from setuptools import setup, find_packages

execfile('facets/version.py')
packages = find_packages(exclude=['*.tests'])

def readme():
    with open('README.rst', 'r') as fp:
        return fp.read()

setup(
    name='facets',
    version=__version__,
    description='Asset manager for Django.',
    long_description=readme(),
    author='Olivier Meunier',
    author_email='olivier@neokraft.net',
    url='https://github.com/olivier-m/django-facets',
    license='MIT License',
    keywords='django assets css javascript compression',
    install_requires=[
        'django>=1.4',
    ],
    packages=packages,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
