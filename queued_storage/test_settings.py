SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'djcelery',
    'queued_storage',
    'queued_storage.tests',
]

import djcelery
djcelery.setup_loader()

BROKER_TRANSPORT = "memory"
CELERY_IGNORE_RESULT = True
CELERYD_LOG_LEVEL = "DEBUG"
CELERY_DEFAULT_QUEUE = "queued_storage"

TEST_RUNNER = 'discover_runner.DiscoverRunner'
