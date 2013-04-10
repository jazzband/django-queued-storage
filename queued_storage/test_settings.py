SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'queued_storage',
    'queued_storage.tests',
]

TEST_RUNNER = 'discover_runner.DiscoverRunner'

SECRET_KEY = 'top_secret'
