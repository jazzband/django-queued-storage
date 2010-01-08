import urllib 

from django.core.cache import cache
from django.core.files.storage import get_storage_class, Storage

from queued_storage.storages.tasks import SaveToRemoteTask

QUEUED_REMOTE_STORAGE_CACHE_KEY_PREFIX = 'queued_remote_storage_'

class QueuedRemoteStorage(Storage):
    def __init__(self, local, remote, cache_prefix=QUEDED_REMOTE_STORAGE_CACHE_KEY_PREFIX):
        self.local_class = local
        self.local = get_storage_class(self.local_class)()
        self.remote_class = remote
        self.remote = get_storage_class(self.remote_class)()
        self.cache_prefix = cache_prefix

    def get_storage(self, name):
        cache_result = cache.get(self.get_cache_key(name))
        if cache_result:
            return self.remote 
        elif cache_result is None:
            if self.remote.exists(name):
                cache.set(self.get_cache_key(name), True)
                return self.remote   
        return self.local

    def get_cache_key(self, name):
        return '%s%s' % (self.cache_prefix, urllib.quote(name))
    
    def using_local(self, name):
        return self.get_storage(name) is self.local
        
    def using_remote(self, name):
        return self.get_storage(name) is self.remote
    
    def open(self, name, **kwargs):
        return self.local.open(name, **kwargs)   
    
    def save(self, name, content):
        cache.set(self.get_cache_key(name), False)
        name = self.local.save(name, content)
        SaveToRemoteTask.delay(name, self.local_class, self.remote_class, self.get_cache_key(name))
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