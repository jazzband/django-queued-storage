import urllib

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject

from queued_storage.conf import settings
from queued_storage.utils import import_attribute


class LazyBackend(SimpleLazyObject):

    def __init__(self, import_path):
        cls = import_attribute(import_path)
        super(LazyBackend, self).__init__(lambda: cls())


class QueuedStorage(object):
    """
    Base class for queued storages. You can use this to specify your own
    backends.

    :param local: local storage class to transfer from
    :type local: dotted import path or :class:`~django:django.core.files.storage.Storage` instance
    :param remote: remote storage class to transfer to
    :type remote: dotted import path or :class:`~django:django.core.files.storage.Storage` instance
    :param cache_prefix: prefix to use in the cache key
    :type cache_prefix: str
    :param delayed: whether the transfer task should be executed automatically
    :type delayed: bool
    :param task: Celery task to use for the transfer
    :type task: dotted import path or :class:`~celery:celery.task.Task` subclass
    """
    #: The local storage class to use. Either a dotted path (e.g.
    #: ``'django.core.files.storage.FileSystemStorage'``) or a
    #: :class:`~django:django.core.files.storage.Storage` subclass.
    local = None

    #: The local storage class to use. Either a dotted path (e.g.
    #: ``'django.core.files.storage.FileSystemStorage'``) or a
    #: :class:`~django:django.core.files.storage.Storage` subclass.
    remote = None

    #: The Celery task class to use to transfer files from the local
    #: to the remote storage. Either a dotted path (e.g.
    #: ``'queued_storage.tasks.Transfer'``) or a
    #: :class:`~celery:celery.task.Task` subclass.
    task = 'queued_storage.tasks.Transfer'

    #: If set to ``True`` the backend will *not* transfer files to the remote
    #: location automatically, but instead requires manual intervention by the
    #: user with the :meth:`~queued_storage.backends.QueuedStorage.transfer`
    #: method.
    #:
    delayed = False

    #: The cache key prefix to use when saving the which storage backend
    #: to use, local or remote (default see
    #: :attr:`~queued_storage.conf.settings.QUEUED_STORAGE_CACHE_PREFIX`)
    cache_prefix = settings.QUEUED_STORAGE_CACHE_PREFIX

    def __init__(self, local=None, remote=None, cache_prefix=None,
                 delayed=None, task=None):
        self.local = self._load_backend('local', local)
        self.remote = self._load_backend('remote', remote)
        self.task = self._load_backend('task', task, import_attribute)
        if delayed is not None:
            self.delayed = delayed
        if cache_prefix is not None:
            self.cache_prefix = cache_prefix

    def _load_backend(self, name, backend=None, handler=LazyBackend):
        if backend is None:
            backend = getattr(self, name, None)
        if isinstance(backend, basestring):
            backend = handler(backend)
        elif backend is None:
            raise ImproperlyConfigured("The QueuedStorage class '%s' doesn't "
                                       "specify a %s backend." % (self, name))
        return backend

    def get_storage(self, name):
        """
        Returns the storage backend instance responsible for the file
        with the given name (either local or remote). This method is
        used in most of the storage API methods.

        :param name: file name
        :type name: str
        :rtype: :class:`~django:django.core.files.storage.Storage`
        """
        cache_result = cache.get(self.get_cache_key(name))
        if cache_result:
            return self.remote
        elif cache_result is None and self.remote.exists(name):
            cache.set(self.get_cache_key(name), True)
            return self.remote
        else:
            return self.local

    def get_cache_key(self, name):
        """
        Returns the cache key for the given file name.

        :param name: file name
        :type name: str
        :rtype: str
        """
        return '%s_%s' % (self.cache_prefix, urllib.quote(name))

    def using_local(self, name):
        """
        Determines for the file with the given name whether
        the local storage is current used.

        :param name: file name
        :type name: str
        :rtype: bool
        """
        return self.get_storage(name) is self.local

    def using_remote(self, name):
        """
        Determines for the file with the given name whether
        the remote storage is current used.

        :param name: file name
        :type name: str
        :rtype: bool
        """
        return self.get_storage(name) is self.remote

    def open(self, name, mode='rb'):
        """
        Retrieves the specified file from storage.

        :param name: file name
        :type name: str
        :param mode: mode to open the file with
        :type mode: str
        :rtype: :class:`~django:django.core.files.File`
        """
        return self.get_storage(name).open(name, mode)

    def save(self, name, content):
        """
        Saves the given content with the given name using the local
        storage. If the :attr:`~queued_storage.backends.QueuedStorage.delayed`
        attribute is ``True`` this will automatically call the
        :meth:`~queued_storage.backends.QueuedStorage.transfer` method
        queuing the transfer from local to remote storage.

        :param name: file name
        :type name: str
        :param content: content of the file specified by name
        :type content: :class:`~django:django.core.files.File`
        :rtype: str
        """
        cache_key = self.get_cache_key(name)
        cache.set(cache_key, False)
        name = self.local.save(name, content)

        # Pass on the cache key to prevent duplicate cache key creation,
        # we save the result in the storage to be able to test for it
        if not self.delayed:
            self.result = self.transfer(name, cache_key=cache_key)
        return name

    def transfer(self, name, cache_key=None):
        """
        Transfers the file with the given name to the remote storage
        backend by queuing the task.

        :param name: file name
        :type name: str
        :param cache_key: the cache key to set after a successful task run
        :type cache_key: str
        :rtype: task result
        """
        if cache_key is None:
            cache_key = self.get_cache_key(name)
        return self.task.delay(name, self.local, self.remote, cache_key)

    def get_valid_name(self, name):
        """
        Returns a filename, based on the provided filename, that's suitable
        for use in the current storage system.

        :param name: file name
        :type name: str
        :rtype: str
        """
        return self.get_storage(name).get_valid_name(name)

    def get_available_name(self, name):
        """
        Returns a filename that's free on the current storage system, and
        available for new content to be written to.

        :param name: file name
        :type name: str
        :rtype: str
        """
        return self.get_storage(name).get_available_name(name)

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.

        :param name: file name
        :type name: str
        :rtype: str
        """
        return self.get_storage(name).path(name)

    def delete(self, name):
        """
        Deletes the specified file from the storage system.

        :param name: file name
        :type name: str
        """
        return self.get_storage(name).delete(name)

    def exists(self, name):
        """
        Returns ``True`` if a file referened by the given name already exists
        in the storage system, or False if the name is available for a new
        file.

        :param name: file name
        :type name: str
        :rtype: bool
        """
        return self.get_storage(name).exists(name)

    def listdir(self, name):
        """
        Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.

        :param name: file name
        :type name: str
        :rtype: tuple
        """
        return self.get_storage(name).listdir(name)

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.

        :param name: file name
        :type name: str
        :rtype: int
        """
        return self.get_storage(name).size(name)

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a Web browser.

        :param name: file name
        :type name: str
        :rtype: str
        """
        return self.get_storage(name).url(name)

    def accessed_time(self, name):
        """
        Returns the last accessed time (as datetime object) of the file
        specified by name.

        :param name: file name
        :type name: str
        :rtype: :class:`~python:datetime.datetime`
        """
        return self.get_storage(name).accessed_time(name)

    def created_time(self, name):
        """
        Returns the creation time (as datetime object) of the file
        specified by name.

        :param name: file name
        :type name: str
        :rtype: :class:`~python:datetime.datetime`
        """
        return self.get_storage(name).created_time(name)

    def modified_time(self, name):
        """
        Returns the last modified time (as datetime object) of the file
        specified by name.

        :param name: file name
        :type name: str
        :rtype: :class:`~python:datetime.datetime`
        """
        return self.get_storage(name).modified_time(name)


class QueuedFileSystemStorage(QueuedStorage):
    """
    A :class:`~queued_storage.QueuedStorage` subclass which conveniently uses
    :class:`~django:django.core.files.storage.FileSystemStorage` as the local
    storage.
    """
    def __init__(self, local='django.core.files.storage.FileSystemStorage', *args, **kwargs):
        super(QueuedFileSystemStorage, self).__init__(local=local, *args, **kwargs)


class QueuedS3BotoStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``S3BotoStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.s3boto.S3BotoStorage', *args, **kwargs):
        super(QueuedS3BotoStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedCouchDBStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``CouchDBStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.couchdb.CouchDBStorage', *args, **kwargs):
        super(QueuedCouchDBStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedDatabaseStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``DatabaseStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.database.DatabaseStorage', *args, **kwargs):
        super(QueuedDatabaseStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedFTPStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``FTPStorage`` storage of the ``django-storages``
    app as the remote storage.
    """
    def __init__(self, remote='storages.backends.ftp.FTPStorage', *args, **kwargs):
        super(QueuedFTPStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedMogileFSStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``MogileFSStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.mogile.MogileFSStorage', *args, **kwargs):
        super(QueuedMogileFSStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedGridFSStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``GridFSStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.mongodb.GridFSStorage', *args, **kwargs):
        super(QueuedGridFSStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedCloudFilesStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``CloudFilesStorage`` storage of the
    ``django-storages`` app as the remote storage.
    """
    def __init__(self, remote='storages.backends.mosso.CloudFilesStorage', *args, **kwargs):
        super(QueuedCloudFilesStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedSFTPStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``SFTPStorage`` storage of the ``django-storages``
    app as the remote storage.
    """
    def __init__(self, remote='storages.backends.sftpstorage.SFTPStorage', *args, **kwargs):
        super(QueuedSFTPStorage, self).__init__(remote=remote, *args, **kwargs)
