from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import get_storage_class

from celery.registry import tasks
from celery.task import Task

MAX_RETRIES = getattr(settings, 'QUEUED_REMOTE_STORAGE_RETRIES', 5)
RETRY_DELAY = getattr(settings, 'QUEUED_REMOTE_STORAGE_RETRY_DELAY', 60)

class SaveToRemoteTask(Task):
    max_retries = MAX_RETRIES
    default_retry_delay = RETRY_DELAY

    def run(self, name, local, remote, cache_key, **kwargs):
        local_storage = get_storage_class(local)()
        remote_storage = get_storage_class(remote)()

        try:
            remote_storage.save(name, local_storage.open(name))
        except:
            # something went wrong while uploading the file, retry
            logger = self.get_logger(**kwargs)
            logger.exception("Unable to save '%s' to remote storage. About "
                    "to retry." % name)
            self.retry([name, local, remote, cache_key], **kwargs)
            return False
    
        cache.set(cache_key, True)
        return True

tasks.register(SaveToRemoteTask)
