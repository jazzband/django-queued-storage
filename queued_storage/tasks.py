from celery.registry import tasks
from celery.task import Task
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import get_storage_class


MAX_RETRIES = getattr(settings, 'QUEUED_REMOTE_STORAGE_RETRIES', 5)
RETRY_DELAY = getattr(settings, 'QUEUED_REMOTE_STORAGE_RETRY_DELAY', 60)

class Transfer(Task):
    max_retries = MAX_RETRIES
    default_retry_delay = RETRY_DELAY
    
    def run(self, name, local_class, remote_class, cache_key,
        local_args, local_kwargs, remote_args, remote_kwargs, **kwargs):
        
        local = local_class(*local_args, **local_kwargs)
        remote = remote_class(*remote_args, **remote_kwargs)
        
        result = self.transfer(name, local, remote, **kwargs)
        
        if result:
            cache.set(cache_key, True)
        else:
            self.retry([name, local_class, remote_class, cache_key,
                local_args, local_kwargs, remote_args, remote_kwargs], **kwargs)
    
        return result
    
    def transfer(self, name, local, remote, **kwargs):
        try:
            remote.save(name, local.open(name))
            return True
        except Exception, e:
            logger = self.get_logger(**kwargs)
            logger.exception("Unable to save '%s' to remote storage. About "
                "to retry." % name)
            logger.exception(e)
            return False

class TransferAndDelete(Transfer):
    def transfer(self, name, local, remote, **kwargs):
        result = super(TransferAndDelete, self).transfer(name, local, remote, **kwargs)

        if result:
            local.delete(name)
        
        return result

tasks.register(Transfer)
tasks.register(TransferAndDelete)
