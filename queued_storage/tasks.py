from django.core.cache import cache
from django.core.files.storage import get_storage_class

from celery.registry import tasks
from celery.task import Task

class SaveToRemoteTask(Task):
    def run(self, name, local, remote, cache_key):
        local_storage = get_storage_class(local)()
        remote_storage = get_storage_class(remote)()
        remote_storage.save(name, local_storage.open(name))
        cache.set(cache_key, True)
        return True
        
tasks.register(SaveToRemoteTask)