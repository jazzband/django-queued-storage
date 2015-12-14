Changelog
=========

v0.8 (2015-12-14)
-----------------

- Added Django 1.9 support

v0.7.2 (2015-12-02)
-------------------

- Documentation config fixes.

v0.7.1 (2015-12-02)
-------------------

- Fix dependency on django-appconf.

- Minor code cleanup.

v0.7 (2015-12-02)
-----------------

- Dropping Django 1.6 support
- Dropping Python 2.6 and 3.2 support
- Switched testing to use tox and py.test
- Added Python 3 support
- Switched to using `setuptools_scm <https://pypi.python.org/pypi/setuptools_scm>`_
- Transfered to Jazzband: https://github.com/jazzband/django-queued-storage
- Tests can be found at: http://travis-ci.org/jazzband/django-queued-storage

v0.6 (2012-05-24)
-----------------

- Added ``file_transferred`` signal that is called right after a file has been
  transfered from the local to the remote storage.

- Switched to using `django-discover-runner`_ and Travis for testing:
  http://travis-ci.org/jezdez/django-queued-storage

.. _`django-discover-runner`: http://pypi.python.org/pypi/django-discover-runner

v0.5 (2012-03-19)
-----------------

- Fixed retrying in case of errors.

- Dropped Python 2.5 support as Celery has dropped it, too.

- Use django-jenkins.

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
