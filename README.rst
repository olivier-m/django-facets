Introduction
============

Django facets is an assets manager providing a cache manager for static files, CSS, Javascript,
images compression and a collection (concatenation) system for CSS and JavaScript.

This new version uses Django static storage system.


Installation
============

- Download the package and type ``python setup.py install``
- Add ``django.contrib.staticfiles`` and ``facets`` to your ``INSTALLED_APPS``
- Set ``STATICFILES_STORAGE`` setting to ``facets.storage.FacetsFilesStorage``


Configuration
=============

Django facets needs some configuration settings.

FACETS_ACTIVE
-------------

This setting enables cache. Its default value is the negation of ``DEBUG`` setting. You can set
it manualy if you want to test your cache in debug mode.

FACETS_STORE
------------

Django Facets keeps track of cached files in a JSON file. By default, it is located in
``STATIC_ROOT/store.json`` but you can set it to any place you want.

FACETS_HANDLERS
---------------

A list of handlers. The default value is::

  (
      'facets.handlers.CssUrls',
  )

These handlers are called during cache creation. You should keep ``facets.handler.CssUrls`` at first
position as it is the one responsible for URL translation in CSS files.

See handlers_ section.


Usage
=====

All static files should be handled as with `Django staticfiles
<https://docs.djangoproject.com/en/1.4/ref/contrib/staticfiles/>`_.

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
  each tag: rel, type, media
* With ``script`` tags, the following attributes must have the same values on
  each tag: type

Collect
-------

Before using the cache, you should run ``./manage.py collectstatic``. This
command generates cached files.

You could run this command during project deployment.

Development mode
----------------

You can test your project with cached files during development.

- Set ``FACETS_ACTIVE`` setting to ``True``
- Set ``DEBUG`` setting to ``True`` (not required)

Then, you have to modify your ``urls.py`` file like this:

::

  from facets.urls import facets_urlpatterns

  if settings.DEBUG:
    if settings.FACETS_ACTIVE:
        urlpatterns += facets_urlpatterns()
    else:
        urlpatterns += staticfiles_urlpatterns()

Finally, start your development server with ``--nostatic`` option.



.. _handlers:

Handlers
========

Handlers are classes that will be called after cached files creation. On each file, every defined
and applicable handler is called. Here is a list of available handlers:


facets.handlers.CssUrls
-----------------------

:Scope: ``*.css``

This handler transforms every URL found in CSS files to point to cached files version. For
example, this rule::

  h1 {
      background: url(../img/title.png);
  }

would become::

  h1 {
      background: url("/static/img/title-e221e1b36656.png");
  }

**Note**: It is recommanded you always set this handler.

facets.handlers.CssMin
----------------------

:Scope: ``*.css``

This handler minifies CSS files using `cssmin <https://github.com/zacharyvoase/cssmin>`_.

facets.handlers.JsMin
---------------------

:Scope: ``*.js``

This handler minifies JavaScript files using `jsmin <http://pypi.python.org/pypi/jsmin>`_.

facets.handlers.UglifyJs
------------------------

:Scope: ``*.js``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | eg. ``["/usr/bin/env", "node", "/path/to/uglifyjs", "--ascii"]``

This handler minifies JavaScript files using `UglifyJs 2 <https://github.com/mishoo/UglifyJS2>`_.

facets.handlers.GoogleClosureCompiler
-------------------------------------

:Scope: ``*.js``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | eg. ``["/usr/bin/java", "-jar", "/path/to/google-closure-compiler.jar"]``

This handler minifies JavaScript files using `Google Closure Compiler
<https://developers.google.com/closure/compiler/>`_.

facets.handlers.YuiJs
---------------------

:Scope: ``*.js``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | eg. ``["/usr/bin/java", "-jar", "/path/to/yuicompressor.jar"]``

This handler minifies JavaScript files using `Yahoo UI Compressor
<http://developer.yahoo.com/yui/compressor/>`_.

facets.handlers.YuiCss
----------------------

:Scope: ``*.css``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | eg. ``["/usr/bin/java", "-jar", "/path/to/yuicompressor.jar"]``

This handler minifies CSS files using `Yahoo UI Compressor
<http://developer.yahoo.com/yui/compressor/>`_.

facets.handlers.OptiPNG
-----------------------

:Scope: ``*.png``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | default: ``["/usr/bin/env", "optipng", "-o7", "-nc"]``

This handler optimizes PNG files using `OptiPNG <http://optipng.sourceforge.net/>`_.

facets.handlers.AdvPNG
----------------------

:Scope: ``*.png``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | default: ``["/usr/bin/env", "advpng", "-z", "-4"]``

This handler optimizes PNG files using `AdvanceCOMP advpng
<http://advancemame.sourceforge.net/doc-advpng.html>`_.

facets.handlers.Jpegtran
------------------------

:Scope: ``*.jpg, *.jpeg``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | default: ``["/usr/bin/env", "jpegtran", "-copy", "none", "-optimize"]``

This handler optimizes JPEG files using `jpegtran <http://jpegclub.org/jpegtran/>`_.

facets.handlers.Jpegoptim
-------------------------

:Scope: ``*.jpg, *.jpeg``
:Options:

  | ``COMMAND``: A list for command to call, with arguments (file name would be added automatically)
  | default: ``["/usr/bin/env", "jpegoptim"]``

This handler optimizes JPEG files using `jpegoptim <http://freshmeat.net/projects/jpegoptim>`_.

facets.handlers.GZip
--------------------

:Scope: ``*.htm, *.html, *js, *.css, *.txt``
:Options: ``LEVEL``: A compression level (0-9). Default to 5.

This handler is a bit special. Instead of updating existing cached file, it creates a gziped copy.
It could be very useful if you configured Nginx with `Gzip Static Module
<http://wiki.nginx.org/HttpGzipStaticModule>`_.

It would of course be better to set this handler in last position in your settings.

License
=======

Django facets is released under the BSD license. See the LICENSE
file for the complete license.
