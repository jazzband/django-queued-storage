from django.conf import settings

from appconf import AppConf

class QueuedStorageConf(AppConf):
    RETRIES = 5
    RETRY_DELAY = 60
    CACHE_KEY = 'queued_remote_storage_'
