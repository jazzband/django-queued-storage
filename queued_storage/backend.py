import urllib

from django.core.cache import cache
from django.core.files.storage import get_storage_class, Storage

from queued_storage.tasks import SaveToRemoteTask

QUEUED_REMOTE_STORAGE_CACHE_KEY_PREFIX = 'queued_remote_storage_'

class QueuedRemoteStorage(Storage):

    def __init__(self, local, remote, cache_prefix=QUEUED_REMOTE_STORAGE_CACHE_KEY_PREFIX, task=None):
        self.local_class = local
        self.remote_class = remote
        self.cache_prefix = cache_prefix
        self._local_instance = None
        self._remote_instance = None

        # allow users to override the task that uploads the image to the remote
        # server
        self.task = task or SaveToRemoteTask

    @property
    def local(self):
        if self._local_instance is None:
            self._local_instance = get_storage_class(self.local_class)()
        return self._local_instance

    @property
    def remote(self):
        if self._remote_instance is None:
            self._remote_instance = get_storage_class(self.remote_class)()
        return self._remote_instance

    def get_storage(self, name):
        cache_result = cache.get(self.get_cache_key(name))

        if cache_result:
            return self.remote
        elif cache_result is None and self.remote.exists(name):
            cache.set(self.get_cache_key(name), True)
            return self.remote

        return self.local

    def get_cache_key(self, name):
        return '%s%s' % (self.cache_prefix, urllib.quote(name))

    def using_local(self, name):
        return self.get_storage(name) is self.local

    def using_remote(self, name):
        return self.get_storage(name) is self.remote

    def open(self, name, *args, **kwargs):
        return self.get_storage(name).open(name, *args, **kwargs)

    def save(self, name, content):
        cache.set(self.get_cache_key(name), False)
        name = self.local.save(name, content)

        self.task.delay(name, self.local_class, self.remote_class, self.get_cache_key(name))

        return name

    def get_valid_name(self, name):
        return self.get_storage(name).get_valid_name(name)

    def get_available_name(self, name):
        return self.get_storage(name).get_available_name(name)

    def path(self, name):
        return self.get_storage(name).path(name)

    def delete(self, name):
        return self.get_storage(name).delete(name)

    def exists(self, name):
        return self.get_storage(name).exists(name)

    def listdir(self, name):
        return self.get_storage(name).listdir(name)

    def size(self, name):
        return self.get_storage(name).size(name)

    def url(self, name):
        return self.get_storage(name).url(name)

class FileSystemAndS3Backend(QueuedRemoteStorage):

    def __init__(self, cache_prefix=QUEUED_REMOTE_STORAGE_CACHE_KEY_PREFIX):
        super(FileSystemAndS3Backend, self).__init__(
            local='django.core.files.storage.FileSystemStorage',
            remote='storages.backends.s3boto.S3BotoStorage',
            cache_prefix=cache_prefix
        )

