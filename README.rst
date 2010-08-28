Introduction
============

Django facets provides a simple way to handle your media during development
and in production. It changes media URLs and offers a feature to create
collections (many files becoming one in production).

Here's an example::

  <link rel="stylesheet" href="{% mediafile "base.css" %}" />

During development the ``mediafile`` tag returns ``{{ MEDIA_URL }}base.css``. If the cache is active, the tag returns the cached file's URL.

Installation
============

Download the package and type ``python setup.py install``. Then, add
``facets`` to your ``INSTALLED_APPS``.

Configuration
=============

Django facets needs some configuration settings.

MEDIA_CACHE_ACTIVE
------------------

This setting enables cache. You should set it to True when in production.

MEDIA_CACHE_ROOT
----------------

The full path to your cached files.

MEDIA_CACHE_URL
---------------

URL to your cached files.

MEDIA_CACHE_STORE
-----------------

After media generation, Django facets creates a ``store.py`` file. By default,
it is located in ``MEDIA_CACHE_ROOT`` but you can set it to any place you
want.

MEDIA_CACHE_HANDLERS
--------------------

A dictionnary of handlers by file types. The default value is::

  {
      'css': (
          'facets.handlers.CssUrls',
          'facets.handlers.CssMin',
      ),
      'js': (
          'facets.handlers.UglifyJs',
      ),
  }

These handlers are called during cache creation. You should not remove
``CssUrls`` handler as it is the one responsible for URL translation in CSS
files.

MEDIA_CACHE_UGLIFYJS
--------------------

If you want to use ``UglifyJs`` handler, you should first install `UglifyJs
<http://github.com/mishoo/UglifyJS>`_ (and node.js) and then give its path in
this setting.

Usage
=====

Links to media
--------------

When you need a media URL, use ``mediafile`` template tag. Here's an example::

  {% load mediafiles %}
  <link rel="stylesheet" href="{% mediafile "css/my.css"} %}" />
  <script src="{% mediafile "js/script.js" %}"></script>

Collections
-----------

Collections are files you want to concatenate while in production. To create
a collection, you should use the ``mediacollection`` template tag. Here's an
example::

  {% load mediafiles %}
  
  {% mediacollection "css/main.css" %}
    <link rel="stylesheet" href="{% mediafile "css/reset.css" %}" />
    <link rel="stylesheet" href="{% mediafile "css/screen.css" %}" />
  {% endmediacollection %}

The argument of the tag is the collection's final name.

Collections follow some rules:

* Only for ``link`` and ``script`` HTML tags.
* You can't mix ``link`` and ``script`` tags together.
* With ``link`` tags, the following attributes must have the same values on
  each tag: rel, type, media
* With ``script`` tags, the following attributes must have the same values on
  each tag: type

Management command
==================

Before using the cache, you should run ``./manage.py generate_media``. This
command generates cached files.

You could run this command during project deployment.

Writing your own handlers
=========================

Writing a handler is quite easy. It should be a class that inherits
``facets.handlers.BaseHandler`` and implements a ``render`` method. This
method returns the modified data or nothing if you don't want any
transformation.

License
=======

Django facets is released under the BSD license. See the LICENSE
file for the complete license.
