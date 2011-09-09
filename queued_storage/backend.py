from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import get_storage_class
from queued_storage.tasks import Transfer
import urllib

CACHE_PREFIX = getattr(settings, 'QUEUED_STORAGE_CACHE_KEY', 'queued_remote_storage_')

class QueuedRemoteStorage(object):

    def __init__(self, local_class, remote_class, cache_prefix=CACHE_PREFIX, task=None,
            local_args=None, local_kwargs=None, remote_args=None, remote_kwargs=None):
        
        self.local_class = local_class
        self.local_args = local_args or ()
        self.local_kwargs = local_kwargs or {}
        
        self.remote_class = remote_class
        self.remote_args = remote_args or ()
        self.remote_kwargs = remote_kwargs or {}
                
        self.cache_prefix = cache_prefix
        
        self._local_instance = None
        self._remote_instance = None

        # Allow users to override the remote transfer task
        self.task = task or Transfer

    def _get_storage_obj(self, klass, args, kwargs):
        klass = get_storage_class(klass)
        return klass(*args, **kwargs)

    @property
    def local(self):
        if self._local_instance is None:
            self._local_instance = self._get_storage_obj(
                self.local_class, self.local_args, self.local_kwargs
            )            
        return self._local_instance

    @property
    def remote(self):
        if self._remote_instance is None:
            self._remote_instance = self._get_storage_obj(
                self.remote_class, self.remote_args, self.remote_kwargs
            )            
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

        self.result = self.transfer(name)

        return name

    def transfer(self, name):
        local_class = get_storage_class(self.local_class)
        remote_class = get_storage_class(self.remote_class)
        
        return self.task.delay(name, local_class, remote_class, self.get_cache_key(name),
            self.local_args, self.local_kwargs, self.remote_args, self.remote_kwargs)
        
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
    
    def accessed_time(self, name):
        return self.get_storage(name).accessed_time(name)
    
    def created_time(self, name):
        return self.get_storage(name).created_time(name)
    
    def modified_time(self, name):
        return self.get_storage(name).modified_time(name)

class DoubleFilesystemStorage(QueuedRemoteStorage):
    def __init__(self, **kwargs):
        super(DoubleFilesystemStorage, self).__init__(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            **kwargs)

class S3Storage(QueuedRemoteStorage):
    def __init__(self, **kwargs):
        super(S3Storage, self).__init__(
            'django.core.files.storage.FileSystemStorage',
            'storages.backends.s3boto.S3BotoStorage',
            **kwargs
        )

class DelayedStorage(QueuedRemoteStorage):
    def save(self, name, content):
        cache.set(self.get_cache_key(name), False)
        name = self.local.save(name, content)
        return name

