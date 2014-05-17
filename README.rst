=============
Django Facets
=============

Features
========

Django facets is an assets manager providing a cache manager for static files, CSS, Javascript,
images compression and a collection (concatenation) system for CSS and JavaScript.

This new version uses Django static storage system.


Installation
============

- Download the package and type ``python setup.py install``
- Add ``django.contrib.staticfiles`` and ``facets`` to your ``INSTALLED_APPS``
- Set ``STATICFILES_STORAGE`` setting to ``facets.storages.FacetsFilesStorage``
- Add, **in first position** ``facets.finders.FacetsFinder`` to ``STATICFILES_FINDERS`` setting


Configuration
=============

Django facets needs some configuration settings.

FACETS_ENABLED
--------------

This setting enables cache. Its default value is the negation of ``DEBUG`` setting. You can set
it manualy if you want to test your cache in debug mode.

CACHES
------

Django Facets keeps track of cached files using Django cache system. It tries to use the cache
named "facets" and falls back to default. Here a configuration example::

  CACHES = CACHES = {
    'default': {
        # Whatever you want
    },
    'facets': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/path/to/directory'
    }
}

FACETS_HANDLERS
---------------

A list of handlers. The default value is::

  (
      'facets.processors.css.CssUrlsProcessor',
  )

These handlers are called during static files collect and/or while compiling some files. Order does not matter.

See handlers_ section.


Usage
=====

All static files should be handled as with `Django staticfiles
<https://docs.djangoproject.com/en/1.6/ref/contrib/staticfiles/>`_.

Collections
-----------

Collections are files you want to concatenate while in production. To create
a collection, you should use the ``mediacollection`` template tag. Here's an
example::

  {% load static from staticfiles %}
  {% load facets %}

  {% mediacollection "css/main.css" %}
    <link rel="stylesheet" href="{% static "css/reset.css" %}" />
    <link rel="stylesheet" href="{% static "css/screen.css" %}" />
  {% endmediacollection %}

The argument of the tag is the collection's final name.

Collections follow some rules:

* Only for ``link`` and ``script`` HTML tags.
* You can't mix ``link`` and ``script`` tags together.
* With ``link`` tags, the following attributes must have the same values on
  each tag: ``rel``, ``type``, ``media``
* With ``script`` tags, the following attributes must have the same values on
  each tag: ``type``

Collect
-------

Before using the cache, you should run ``./manage.py collectstatic``. This
command generates cached files.

You could run this command during project deployment. Please note that you MUST restart your
project server after running collectstatic.

.. _handlers:

Handlers
========

Handlers are classes that take responsibility to transform an input file. There are two types of handlers: compilers and processors.

Compilers
---------

Compilers create final files for some preprocessors languages (Less, Sass, CoffeeScript, etc.).
A compiler will be called during *collectstatic* and while serving static files if setting ``FACETS_ENABLED`` is set to ``False`` (usually during development).

Please note that there can be only one compiler by file extension.

facets.compilers.css.LessCompiler
+++++++++++++++++++++++++++++++++

:Extensions: ``less``
:Options:

  | **new_name**: ``{base}.css``
  | **program**: ``/usr/bin/env lessc``
  | **command**: ``{program} - {outfile}``

This compiler compiles Less files using `Less <http://lesscss.org/>`_ preprocessor.

facets.compilers.css.SasscCompiler
++++++++++++++++++++++++++++++++++

:Extensions: ``scss``, ``sass``
:Options:

  | **new_name**: ``{base}.css``
  | **program**: ``/usr/bin/env sassc``
  | **command**: ``{program} -``

This compiler compiles Sass files using `SassC <http://libsass.org/#sassc>`_ preprocessor.

facets.compilers.css.LibSassCompiler
++++++++++++++++++++++++++++++++++++

:Extensions: ``scss``, ``sass``

This compiler compiles Sass files using `libsass-python <http://dahlia.kr/libsass-python/>`_ preprocessor.

facets.compilers.js.CoffeScriptCompiler
+++++++++++++++++++++++++++++++++++++++

:Extensions: ``coffee``
:Options:

  | **new_name**: ``{base}.js``
  | **program**: ``/usr/bin/env coffee``
  | **command**: ``{program} -c --print {infile}``

This compiler compiles CoffeeScript files using `CoffeeScript <http://coffeescript.org/>`_ command.

facets.compilers.js.LiveScriptCompiler
++++++++++++++++++++++++++++++++++++++

:Extensions: ``ls``
:Options:

  | **new_name**: ``{base}.js``
  | **program**: ``/usr/bin/env lsc``
  | **command**: ``{program} -c --print {infile}``

This compiler compiles LiveScript files using `LiveScript <http://livescript.net/>`_ command.

facets.compilers.js.DartCompiler
++++++++++++++++++++++++++++++++

:Extensions: ``dart``
:Options:

  | **new_name**: ``{base}.js``
  | **program**: ``/usr/bin/env dart2js``
  | **command**: ``{program} -o {outfile} {infile}``

This compiler compiles Dart files using `Dart <https://www.dartlang.org/>`_ dart2js.


Processors
----------

Processors are called during *collectstatic*. Their job is usually to optimize files.

facets.processors.css.CssUrlsProcessor
++++++++++++++++++++++++++++++++++++++

:Scope: ``*.css``
:Options: **priority**: -1000 (please don't change it)

This processor transforms every URL found in CSS files to point to cached files version. For
example, this rule::

  h1 {
      background: url(../img/title.png);
  }

would become::

  h1 {
      background: url("/static/img/title-e221e1b36656.png");
  }

**Note**: It is recommended to always have this processor set.

facets.processors.css.CssMinProcessor
+++++++++++++++++++++++++++++++++++++

:Scope: ``*.css``

This processor minifies CSS files using `cssmin <https://github.com/zacharyvoase/cssmin>`_.

facets.processors.js.JsMinProcessor
+++++++++++++++++++++++++++++++++++

:Scope: ``*.js``

This processor minifies JavaScript files using `jsmin <http://pypi.python.org/pypi/jsmin>`_.

facets.processors.js.UglifyJsProcessor
++++++++++++++++++++++++++++++++++++++

:Scope: ``*.js``
:Options:

  | **program**: ``/usr/bin/env uglifyjs``
  | **command**: ``{program} {infile} --ascii -m -c -o {outfile}``

This processor minifies JavaScript files using `UglifyJs 2 <https://github.com/mishoo/UglifyJS2>`_.

facets.processors.js.GoogleClosureProcessor
+++++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.js``
:Options:

  | **program**: ``/usr/bin/env java -jar /path/to/compiler.jar`` (you'll have to change that)
  | **command**: ``{program} {infile}``

This processor minifies JavaScript files using `Google Closure Compiler
<https://developers.google.com/closure/compiler/>`_.

facets.processors.js.YuiJsProcessor
+++++++++++++++++++++++++++++++++++

:Scope: ``*.js``
:Options:

  | **program**: ``/usr/bin/env java -jar /path/to/yuicompressor-xxx.jar`` (you'll have to change that)
  | **command**: ``{program} {infile}``

This processor minifies JavaScript files using `Yahoo UI Compressor
<http://developer.yahoo.com/yui/compressor/>`_.

facets.processors.css.YuiCssProcessor
+++++++++++++++++++++++++++++++++++++

:Scope: ``*.css``
:Options:

  | **program**: ``/usr/bin/env java -jar /path/to/yuicompressor-xxx.jar`` (you'll have to change that)
  | **command**: ``{program} {infile}``

This processor minifies CSS files using `Yahoo UI Compressor
<http://developer.yahoo.com/yui/compressor/>`_.

facets.processors.images.OptiPngProcessor
+++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.png``
:Options:

  | **program**: ``/usr/bin/env optipng``
  | **command**: ``{program} -o7 -nc {infile}``

This processor optimizes PNG files using `OptiPNG <http://optipng.sourceforge.net/>`_.

facets.processors.images.AdvPngProcessor
++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.png``
:Options:

  | **program**: ``/usr/bin/env advpng``
  | **command**: ``{program} -z -4 {infile}``

This processor optimizes PNG files using `AdvanceCOMP advpng
<http://advancemame.sourceforge.net/doc-advpng.html>`_.

facets.processors.images.JpegtranProcessor
++++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.jpg, *.jpeg``
:Options:

  | **program**: ``/usr/bin/env jpegtran``
  | **command**: ``{program} -copy none -optimize {infile}``

This processor optimizes JPEG files using `jpegtran <http://jpegclub.org/jpegtran/>`_.

facets.processors.images.JpegoptimProcessor
+++++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.jpg, *.jpeg``
:Options:

  | **program**: ``/usr/bin/env jpegoptim``
  | **command**: ``{program} -q --strip-all {infile}``

This processor optimizes JPEG files using `jpegoptim <http://freshmeat.net/projects/jpegoptim>`_.

facets.processors.images.GifsicleProcessor
++++++++++++++++++++++++++++++++++++++++++

:Scope: ``*.gif``
:Options:

  | **program**: ``/usr/bin/env gifsicle``
  | **command**: ``{program} --batch -O3 {infile}``

This processor optimizes GIF files using `Gifsicle <http://www.lcdf.org/gifsicle/>`_.

facets.processors.gz.GZipProcessor
++++++++++++++++++++++++++++++++++

:Scope: ``*.htm, *.html, *js, *.css, *.txt, *.eot, *.ttf, *.woff, *.svg``
:Options:

  | **priority**: 1000 (please don't change it)
  | **compresslevel**: A compression level (0-9). Default to 5.

This processor is a bit special. Instead of updating existing cached file, it creates a gziped copy. It could be very useful if you configured Nginx with `Gzip Static Module
<http://wiki.nginx.org/HttpGzipStaticModule>`_.


License
=======

Django facets is released under the BSD license. See the LICENSE
file for the complete license.
