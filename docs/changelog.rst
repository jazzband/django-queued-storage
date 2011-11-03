Changelog
=========

v0.4 (2011-11-03)
-----------------

- Revised storage parameters to fix an incompatibility with Celery regarding
  task parameter passing and pickling.

  It's now *required* to pass the dotted Python import path of the local
  and remote storage backend, as well as a dictionary of options for
  instantiation of those classes (if needed). Passing storage instances
  to the :class:`~queued_storage.backends.QueuedStorage` class is now
  considered an error. For example:

  Old::

      from django.core.files.storage import FileSystemStorage
      from mysite.storage import MyCustomStorageBackend

      my_storage = QueuedStorage(
          FileSystemStorage(location='/path/to/files'),
      	  MyCustomStorageBackend(spam='eggs'))

  New::

    my_storage = QueuedStorage(
      local='django.core.files.storage.FileSystemStorage',
      local_options={'location': '/path/to/files'},
      remote='mysite.storage.MyCustomStorageBackend',
      remote_options={'spam': 'eggs'})

  .. warning::

  	This change is backwards-incompatible if you used the
  	:class:`~queued_storage.backends.QueuedStorage` API.

v0.3 (2011-09-19)
-----------------

- Initial release.
