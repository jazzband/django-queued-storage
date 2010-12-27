django-queued-storage
======================

This is a storage backend that allows you specify a local and a remote storage
backend. It will upload locally and then queue up the transfer to your remote
backend. If any request for the file occurs before the file gets to the remote
backend your local backend will be used. Once the file has been successfully
transferred to the remote backend all request for the file will use the remote
backend.

This backend requires celery_, which is used for the queuing.

.. _celery: http://celeryproject.org/

Example
--------

The ``QueuedRemoteStorage`` class can be can be used as a drop-in replacement
wherever ``django.core.file.storage.Storage`` might otherwise be required. It
has all the standard methods, along with a couple of extra ones for checking
if the file has been uploaded to the remote storage or not::

    >>> from queued_storage.backend import QueuedRemoteStorage
    >>> storage = QueuedRemoteStorage(
    ... local='django.core.files.storage.FileSystemStorage',
    ... remote='backends.s3boto.S3BotoStorage')
    >>> storage.save(fname, file)
    >>> storage.url(fname)
    u'/uploads/myfile.jpg'
    >>> storage.using_local(fname)
    True
    >>> storage.using_remote(fname)
    False
    >>> time.sleep(30)
    >>> storage.url(fname)
    u'http://mybucket.s3.amazonaws.com/uploads/myfile.jpg'
    >>> storage.using_local(fname)
    False
    >>> storage.using_remote(fname)
    True

At this point, the local copy of the file could be removed, as all references
will be to the remote copy.

Typically, however, you won't need to use the class quite this directly.
Instead, pass in an instance of the class as the ``storage`` argument to
``django.db.models.FileField`` or ``django.db.models.ImageField`` and it will
be used transparently.

Installation
-------------

1. Make sure celery is installed and running: http://ask.github.com/celery/introduction.html

2. Make sure you have a cache backend set up.

3. Add the backend to the storage argument of a FileField::
		
		image = ImageField(storage=QueuedRemoteStorage(local='django.core.files.storage.FileSystemStorage',
		                   remote='backends.s3boto.S3BotoStorage'), upload_to='uploads')

