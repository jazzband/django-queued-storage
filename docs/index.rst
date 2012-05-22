.. include:: ../README.rst

Usage
-----

The :class:`~queued_storage.backends.QueuedStorage` can be used as a drop-in
replacement wherever using :class:`django:django.core.files.storage.Storage`
might otherwise be required.

This example is using django-storages_ for the remote backend::

    from django.db import models
    from queued_storage.backends import QueuedStorage
    from storages.backends.s3boto import S3BotoStorage

    queued_s3storage = QueuedStorage(
        'django.core.files.storage.FileSystemStorage',
        'storages.backends.s3boto.S3BotoStorage')

    class MyModel(models.Model):
        image = ImageField(storage=queued_s3storage)

.. _django-storages: http://code.welldev.org/django-storages/

Settings
--------

.. currentmodule:: queued_storage.conf.settings

.. attribute:: QUEUED_STORAGE_CACHE_PREFIX

    :Default: ``'queued_storage'``

    The cache key prefix to use when caching the storage backends.

.. attribute:: QUEUED_STORAGE_RETRIES

    :Default: ``5``

    How many retries should be attempted before aborting.

.. attribute:: QUEUED_STORAGE_RETRY_DELAY

    :Default: ``60``

    The delay between retries in seconds.

Reference
---------

For further details see the reference documentation:

.. toctree::
   :maxdepth: 1

   backends
   fields
   tasks
   signals
   changelog

Issues
------

For any bug reports and feature requests, please use the
`Github issue tracker`_.

.. _`Github issue tracker`: https://github.com/jezdez/django-queued-storage/issues
