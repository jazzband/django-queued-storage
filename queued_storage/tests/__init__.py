from django.conf import settings

if 'queued_storage.tests' in settings.INSTALLED_APPS:
    from .tests import StorageTests
