"""
For simplicity and to avoid requiring a paid-for account on some cloud
storage system testing is conducted against two local storage backends. Since
the QueuedStorage backend is truly agnostic about the local and remote
storage systems, this should work as transparently as using one (or even two!)
remote storage systems.
"""

import tempfile
from os import path

from django.core.files.storage import Storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings as django_settings
from django.test import TestCase

from queued_storage.backends import QueuedStorage
from queued_storage.conf import settings

from . import models
from . import backends


class StorageTests(TestCase):
    def setUp(self):
        self.old_celery_always_eager = getattr(settings, 'CELERY_ALWAYS_EAGER', False)
        settings.CELERY_ALWAYS_EAGER = True

        # Note that starting with Django>=1.10, Storages APIs don't allow to write outside MEDIA_ROOT
        # django_settings.MEDIA_ROOT = tempfile.mkdtemp()
        # django_settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

        self.test_file_name = 'dummy_test_file_name.txt'
        self.test_file = SimpleUploadedFile(self.test_file_name, b'these bytes are the file content!')

    def tearDown(self):
        settings.CELERY_ALWAYS_EAGER = self.old_celery_always_eager

    def test_storage_init(self):
        """
        Make sure that creating a QueuedStorage object works
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage')

        self.assertIsInstance(storage, QueuedStorage)
        self.assertEqual(backends.LocalStorage, storage.local.__class__)
        self.assertEqual(backends.RemoteStorage, storage.remote.__class__)

    def test_storage_cache_key(self):
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            cache_prefix='test_cache_key')

        self.assertEqual(storage.cache_prefix, 'test_cache_key')

    def test_storage_methods(self):
        """
        Make sure that QueuedStorage implements all the methods of the base Storage class.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage')

        file_storage = Storage()

        for attr in dir(file_storage):
            method = getattr(file_storage, attr)

            if not callable(method):
                continue

            method = getattr(storage, attr, False)
            self.assertTrue(callable(method),
                            "QueuedStorage has no method '%s'" % attr)

    def test_storage_simple_local_save_then_transfer(self):
        """
        Make sure that saving to remote location actually works. Be careful, by default the transfer task does NOT include a local delete.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='queued_storage.tasks.Transfer',
            delayed=True)

        models.TestModel.queued_file_field_use_storage(storage)

        obj = models.TestModel(queued_file=self.test_file)

        self.assertEqual(storage, obj.queued_file.storage)
        self.assertIsNone(getattr(obj.queued_file.storage, 'result', None))

        obj.save()

        self.assertTrue(obj.queued_file.is_stored_locally())
        self.assertFalse(obj.queued_file.is_stored_remotely())

        # We shouldn't have to test this, as it is purely internal implementation of QueuedStorage. But because, it is
        # FileSystemStorage under the hood, we could have a sneak peak...
        upload_to_folder_name = models.TestModel._meta.get_field('queued_file').upload_to
        sub_folder_file_path = path.join(upload_to_folder_name, self.test_file_name)

        # Test if file is here.
        self.assertTrue(path.isfile(obj.queued_file.storage.local.path(sub_folder_file_path)))
        # Test if file is, of course, not there.
        self.assertFalse(path.isfile(obj.queued_file.storage.remote.path(sub_folder_file_path)))

        # self.assertEqual(storage.listdir('test')[1], [self.test_file_name])
        # self.assertEqual(storage.size(subdir_path), os.stat(self.test_file_path).st_size)
        # self.assertEqual(storage.url(self.test_file_name), self.test_file_name)
        # self.assertIsInstance(storage.accessed_time(subdir_path), datetime)
        # self.assertIsInstance(storage.created_time(subdir_path), datetime)
        # self.assertIsInstance(storage.modified_time(subdir_path), datetime)

        # WARNING: By default the transfer task does NOT include a local delete.
        obj.queued_file.transfer()

        self.assertFalse(obj.queued_file.is_stored_locally())
        self.assertTrue(obj.queued_file.is_stored_remotely())

        # Test if file is still here.
        self.assertTrue(path.isfile(obj.queued_file.storage.local.path(sub_folder_file_path)))
        # Test if file is now there too.
        self.assertTrue(path.isfile(obj.queued_file.storage.remote.path(sub_folder_file_path)))

    def test_storage_simple_local_save_then_transfer_and_delete(self):
        """
        Make sure that saving to remote location actually works.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='queued_storage.tasks.TransferAndDelete',
            delayed=True)

        models.TestModel.queued_file_field_use_storage(storage)

        obj = models.TestModel(queued_file=self.test_file)
        obj.save()

        self.assertTrue(obj.queued_file.is_stored_locally())
        self.assertFalse(obj.queued_file.is_stored_remotely())

        obj.queued_file.transfer()

        self.assertTrue(obj.queued_file.is_stored_remotely())
        self.assertFalse(obj.queued_file.is_stored_locally())

    def test_storage_celery_save(self):
        """
        Make sure that saving to remote location actually works.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='queued_storage.tasks.Transfer',
            delayed=False)

        models.TestModel.queued_file_field_use_storage(storage)

        obj = models.TestModel(queued_file=self.test_file)
        obj.save()

        self.assertFalse(obj.queued_file.is_stored_locally())
        self.assertTrue(obj.queued_file.is_stored_remotely())

        # Test that calling transfer at that point has no effects.
        obj.queued_file.transfer()
        self.assertFalse(obj.queued_file.is_stored_locally())
        self.assertTrue(obj.queued_file.is_stored_remotely())

    def test_storage_celery_save_with_delete(self):
        """
        Make sure that saving to remote location actually works.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='queued_storage.tasks.TransferAndDelete',
            delayed=False)

        models.TestModel.queued_file_field_use_storage(storage)

        obj = models.TestModel(queued_file=self.test_file)
        obj.save()

        self.assertFalse(obj.queued_file.is_stored_locally())
        self.assertTrue(obj.queued_file.is_stored_remotely())

        # Test that calling transfer at that point has no effects.
        obj.queued_file.transfer()
        self.assertFalse(obj.queued_file.is_stored_locally())
        self.assertTrue(obj.queued_file.is_stored_remotely())

    def test_transfer_returns_boolean(self):
        """
        Make sure an exception is thrown when the transfer task does not return
        a boolean. We don't want to confuse Celery.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='tests.tasks.NoneReturningTransferTask',
            delayed=False)

        models.TestModel.queued_file_field_use_storage(storage)

        obj = models.TestModel(queued_file=self.test_file)
        obj.save()

        self.assertRaises(ValueError, obj.queued_file.storage.result.get, propagate=True)

    def test_transfer_retried(self):
        """
        Make sure the transfer task is retried correctly.
        """
        storage = QueuedStorage(
            'tests.backends.LocalStorage',
            'tests.backends.RemoteStorage',
            task='tests.tasks.RetryingTransferTask',
            delayed=False)

        models.TestModel.queued_file_field_use_storage(storage)
        self.assertFalse(models.TestModel.retried)

        obj = models.TestModel(queued_file=self.test_file)
        obj.save()

        self.assertFalse(obj.queued_file.storage.result.get())
        self.assertTrue(models.TestModel.retried)
