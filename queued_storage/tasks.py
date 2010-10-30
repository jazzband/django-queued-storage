from django.core.cache import cache
from django.core.files.storage import get_storage_class

from celery.registry import tasks
from celery.task import Task

class SaveToRemoteTask(Task):
    max_retries = 5
    default_retry_delay = 60

    def run(self, name, local, remote, cache_key, **kwargs):
        local_storage = get_storage_class(local)()
        remote_storage = get_storage_class(remote)()

        try:
            remote_storage.save(name, local_storage.open(name))
        except:
            # something went wrong while uploading the file, retry
            self.retry([name, local, remote, cache_key], **kwargs)
            return False

        cache.set(cache_key, True)
        return True

tasks.register(SaveToRemoteTask)
