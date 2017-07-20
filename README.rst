django-queued-storage
=====================

.. image:: https://img.shields.io/pypi/v/django-queued-storage.svg
   :alt: PyPi page
   :target: https://pypi.python.org/pypi/django-queued-storage

.. image:: https://img.shields.io/travis/jazzband/django-queued-storage.svg
    :alt: Travis CI Status
    :target: https://travis-ci.org/jazzband/django-queued-storage

.. image:: https://img.shields.io/coveralls/jazzband/django-queued-storage/master.svg
   :alt: Coverage status
   :target: https://coveralls.io/r/jazzband/django-queued-storage

.. image:: https://readthedocs.org/projects/django-queued-storage/badge/?version=latest&style=flat
   :alt: ReadTheDocs
   :target: https://django-queued-storage.readthedocs.io/en/latest/

.. image:: https://img.shields.io/pypi/l/django-queued-storage.svg
   :alt: License BSD

.. image:: https://jazzband.co/static/img/badge.svg
   :target: https://jazzband.co/
   :alt: Jazzband

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
.. _`caching backend`: https://docs.djangoproject.com/en/1.10/topics/cache/#setting-up-the-cache
.. _Celery:  http://celeryproject.org/
