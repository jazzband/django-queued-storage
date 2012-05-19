django-queued-storage
=====================

.. image:: https://secure.travis-ci.org/jezdez/django-queued-storage.png?branch=develop
    :alt: Build Status
    :target: http://travis-ci.org/jezdez/django-queued-storage

This storage backend enables having a local and a remote storage
backend. It will save any file locally and queue a task to transfer it
somewhere else using Celery_.

If the file is accessed before it's transferred, the local copy is
returned.

Installation
------------

::

    pip install django-queued-storage

Configuration
-------------

-  Follow the configuration instructions for
   django-celery_
-  Set up a `caching backend`_
-  Add ``'queued_storage'`` to your ``INSTALLED_APPS`` setting

.. _django-celery: https://github.com/ask/django-celery
.. _`caching backend`: https://docs.djangoproject.com/en/1.3/topics/cache/#setting-up-the-cache
.. _Celery:  http://celeryproject.org/
