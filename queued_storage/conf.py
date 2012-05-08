from django.conf import settings  # noqa

from appconf import AppConf


class QueuedStorageConf(AppConf):
    RETRIES = 5
    RETRY_DELAY = 60
    CACHE_PREFIX = 'queued_storage'
