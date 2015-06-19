import six

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from django.utils.http import urlquote

from queued_storage.conf import settings
from queued_storage.utils import import_attribute, django_version

if django_version()[1] >= 7:
    from django.utils.deconstruct import deconstructible


class LazyBackend(SimpleLazyObject):

    def __init__(self, import_path, options):
        backend = import_attribute(import_path)
        super(LazyBackend, self).__init__(lambda: backend(**options))


class QueuedStorage(object):
    """
    Base class for queued storages. You can use this to specify your own
    backends.

    :param local: local storage class to transfer from
    :type local: str
    :param local_options: options of the local storage class
    :type local_options: dict
    :param remote: remote storage class to transfer to
    :type remote: str
    :param remote_options: options of the remote storage class
    :type remote_options: dict
    :param cache_prefix: prefix to use in the cache key
    :type cache_prefix: str
    :param delayed: whether the transfer task should be executed automatically
    :type delayed: bool
    :param task: Celery task to use for the transfer
    :type task: str
    """
    #: The local storage class to use. A dotted path (e.g.
    #: ``'django.core.files.storage.FileSystemStorage'``).
    local = None

    #: The options of the local storage class, defined as a dictionary.
    local_options = None

    #: The remote storage class to use. A dotted path (e.g.
    #: ``'django.core.files.storage.FileSystemStorage'``).
    remote = None

    #: The options of the remote storage class, defined as a dictionary.
    remote_options = None

    #: The Celery task class to use to transfer files from the local
    #: to the remote storage. A dotted path (e.g.
    #: ``'queued_storage.tasks.Transfer'``).
    task = 'queued_storage.tasks.Transfer'

    #: If set to ``True`` the backend will *not* transfer files to the remote
    #: location automatically, but instead requires manual intervention by the
    #: user with the :meth:`~queued_storage.backends.QueuedStorage.transfer`
    #: method.
    delayed = False

    #: The cache key prefix to use when saving the which storage backend
    #: to use, local or remote (default see
    #: :attr:`~queued_storage.conf.settings.QUEUED_STORAGE_CACHE_PREFIX`)
    cache_prefix = settings.QUEUED_STORAGE_CACHE_PREFIX

    def __init__(self, local=None, remote=None,
                 local_options=None, remote_options=None,
                 cache_prefix=None, delayed=None, task=None):

        self.local_path = local or self.local
        self.local_options = local_options or self.local_options or {}
        self.local = self._load_backend(backend=self.local_path,
                                        options=self.local_options)

        self.remote_path = remote or self.remote
        self.remote_options = remote_options or self.remote_options or {}
        self.remote = self._load_backend(backend=self.remote_path,
                                         options=self.remote_options)

        self.task = self._load_backend(backend=task or self.task,
                                       handler=import_attribute)
        if delayed is not None:
            self.delayed = delayed
        if cache_prefix is not None:
            self.cache_prefix = cache_prefix

    def _load_backend(self, backend=None, options=None, handler=LazyBackend):
        if backend is None:  # pragma: no cover
            raise ImproperlyConfigured("The QueuedStorage class '%s' "
                                       "doesn't define a needed backend." %
                                       (self, backend))
        if not isinstance(backend, six.string_types):
            raise ImproperlyConfigured("The QueuedStorage class '%s' "
                                       "requires its backends to be "
                                       "specified as dotted import paths "
                                       "not instances or classes" % self)
        return handler(backend, options)

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
        return '%s_%s' % (self.cache_prefix, urlquote(name))

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

        # Use a name that is available on both the local and remote storage
        # systems and save locally.
        name = self.get_available_name(name)
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
        return self.task.delay(name, cache_key,
                               self.local_path, self.remote_path,
                               self.local_options, self.remote_options)

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
        Returns a filename that's free on both the local and remote storage
        systems, and available for new content to be written to.

        :param name: file name
        :type name: str
        :rtype: str
        """
        local_available_name = self.local.get_available_name(name)
        remote_available_name = self.remote.get_available_name(name)

        if remote_available_name > local_available_name:
            return remote_available_name
        return local_available_name

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
if django_version()[1] >= 7:
    QueuedStorage = deconstructible(QueuedStorage)


class QueuedFileSystemStorage(QueuedStorage):
    """
    A :class:`~queued_storage.backends.QueuedStorage` subclass which
    conveniently uses
    :class:`~django:django.core.files.storage.FileSystemStorage` as the local
    storage.
    """
    def __init__(self, local='django.core.files.storage.FileSystemStorage', *args, **kwargs):
        super(QueuedFileSystemStorage, self).__init__(local=local, *args, **kwargs)


class QueuedS3BotoStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``S3BotoStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.s3boto.S3BotoStorage', *args, **kwargs):
        super(QueuedS3BotoStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedCouchDBStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``CouchDBStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.couchdb.CouchDBStorage', *args, **kwargs):
        super(QueuedCouchDBStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedDatabaseStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``DatabaseStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.database.DatabaseStorage', *args, **kwargs):
        super(QueuedDatabaseStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedFTPStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``FTPStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.ftp.FTPStorage', *args, **kwargs):
        super(QueuedFTPStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedMogileFSStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``MogileFSStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.mogile.MogileFSStorage', *args, **kwargs):
        super(QueuedMogileFSStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedGridFSStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``GridFSStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.mongodb.GridFSStorage', *args, **kwargs):
        super(QueuedGridFSStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedCloudFilesStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``CloudFilesStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.mosso.CloudFilesStorage', *args, **kwargs):
        super(QueuedCloudFilesStorage, self).__init__(remote=remote, *args, **kwargs)


class QueuedSFTPStorage(QueuedFileSystemStorage):
    """
    A custom :class:`~queued_storage.backends.QueuedFileSystemStorage`
    subclass which uses the ``SFTPStorage`` storage of the
    `django-storages <http://django-storages.readthedocs.org/>`_ app as
    the remote storage.
    """
    def __init__(self, remote='storages.backends.sftpstorage.SFTPStorage', *args, **kwargs):
        super(QueuedSFTPStorage, self).__init__(remote=remote, *args, **kwargs)
