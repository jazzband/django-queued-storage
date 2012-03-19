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
    'django_jenkins',
]

import djcelery
djcelery.setup_loader()

BROKER_TRANSPORT = "memory"
CELERY_IGNORE_RESULT = True
CELERYD_LOG_LEVEL = "DEBUG"
CELERY_DEFAULT_QUEUE = "queued_storage"

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pyflakes',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',
)
