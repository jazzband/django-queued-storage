"""
For simplicity and to avoid requiring a paid-for account on some cloud
storage system testing is conducted against two local storage backends. Since
the QueuedStorage backend is truly agnostic about the local and remote
storage systems, this should work as transparently as using one (or even two!)
remote storage systems.
"""
import os
import shutil
import tempfile
from os import path
from datetime import datetime

from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, Storage
from django.test import TestCase

from queued_storage.backends import QueuedStorage
from queued_storage.conf import settings

from . import models


class StorageTests(TestCase):

    def setUp(self):
        self.old_celery_always_eager = getattr(
            settings, 'CELERY_ALWAYS_EAGER', False)
        settings.CELERY_ALWAYS_EAGER = True
        self.local_dir = tempfile.mkdtemp()
        self.remote_dir = tempfile.mkdtemp()
        tmp_dir = tempfile.mkdtemp()
        self.test_file_name = 'queued_storage.txt'
        self.test_file_path = path.join(tmp_dir, self.test_file_name)
        with open(self.test_file_path, 'a') as test_file:
            test_file.write('test')
        self.test_file = open(self.test_file_path, 'r')
        self.addCleanup(shutil.rmtree, self.local_dir)
        self.addCleanup(shutil.rmtree, self.remote_dir)
        self.addCleanup(shutil.rmtree, tmp_dir)

    def tearDown(self):
        settings.CELERY_ALWAYS_EAGER = self.old_celery_always_eager

    def test_storage_init(self):
        """
        Make sure that creating a QueuedStorage object works
        """
        storage = QueuedStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage')
        self.assertIsInstance(storage, QueuedStorage)
        self.assertEqual(FileSystemStorage, storage.local.__class__)
        self.assertEqual(FileSystemStorage, storage.remote.__class__)

    def test_storage_cache_key(self):
        storage = QueuedStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            cache_prefix='test_cache_key')
        self.assertEqual(storage.cache_prefix, 'test_cache_key')

    def test_storage_methods(self):
        """
        Make sure that QueuedStorage implements all the methods
        """
        storage = QueuedStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage')

        file_storage = Storage()

        for attr in dir(file_storage):
            method = getattr(file_storage, attr)

            if not callable(method):
                continue

            method = getattr(storage, attr, False)
            self.assertTrue(callable(method),
                            "QueuedStorage has no method '%s'" % attr)

    def test_storage_simple_save(self):
        """
        Make sure that saving to remote locations actually works
        """
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            task='queued_storage.tests.tasks.test_task')

        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        self.assertTrue(path.isfile(path.join(self.local_dir, obj.testfile.name)))
        self.assertTrue(path.isfile(path.join(self.remote_dir, obj.testfile.name)))

    def test_storage_celery_save(self):
        """
        Make sure it actually works when using Celery as a task queue
        """
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir))

        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        self.assertTrue(obj.testfile.storage.result.get())
        self.assertTrue(path.isfile(path.join(self.local_dir, obj.testfile.name)))
        self.assertTrue(
            path.isfile(path.join(self.remote_dir, obj.testfile.name)),
            "Remote file is not available.")
        self.assertFalse(storage.using_local(obj.testfile.name))
        self.assertTrue(storage.using_remote(obj.testfile.name))

        self.assertEqual(self.test_file_name,
                         storage.get_valid_name(self.test_file_name))
        self.assertEqual(self.test_file_name,
                         storage.get_available_name(self.test_file_name))

        subdir_path = os.path.join('test', self.test_file_name)
        self.assertTrue(storage.exists(subdir_path))
        self.assertEqual(storage.path(self.test_file_name),
                         path.join(self.local_dir, self.test_file_name))
        self.assertEqual(storage.listdir('test')[1], [self.test_file_name])
        self.assertEqual(storage.size(subdir_path),
                         os.stat(self.test_file_path).st_size)
        self.assertEqual(storage.url(self.test_file_name), self.test_file_name)
        self.assertIsInstance(storage.accessed_time(subdir_path), datetime)
        self.assertIsInstance(storage.created_time(subdir_path), datetime)
        self.assertIsInstance(storage.modified_time(subdir_path), datetime)

        subdir_name = 'queued_storage_2.txt'
        testfile = storage.open(subdir_name, 'w')
        try:
            testfile.write('test')
        finally:
            testfile.close()
        self.assertTrue(storage.exists(subdir_name))
        storage.delete(subdir_name)
        self.assertFalse(storage.exists(subdir_name))

    def test_transfer_and_delete(self):
        """
        Make sure the TransferAndDelete task does what it says
        """
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            task='queued_storage.tasks.TransferAndDelete')

        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        obj.testfile.storage.result.get()

        self.assertFalse(
            path.isfile(path.join(self.local_dir, obj.testfile.name)),
            "Local file is still available")
        self.assertTrue(
            path.isfile(path.join(self.remote_dir, obj.testfile.name)),
            "Remote file is not available.")

    def test_transfer_returns_boolean(self):
        """
        Make sure an exception is thrown when the transfer task does not return
        a boolean. We don't want to confuse Celery.
        """
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            task='queued_storage.tests.tasks.NoneReturningTask')

        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        self.assertRaises(ValueError,
                          obj.testfile.storage.result.get, propagate=True)

    def test_transfer_retried(self):
        """
        Make sure the transfer task is retried correctly.
        """
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            task='queued_storage.tests.tasks.RetryingTask')
        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        self.assertFalse(models.TestModel.retried)

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        self.assertFalse(obj.testfile.storage.result.get())
        self.assertTrue(models.TestModel.retried)

    def test_delayed_storage(self):
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            delayed=True)

        field = models.TestModel._meta.get_field('testfile')
        field.storage = storage

        obj = models.TestModel(testfile=File(self.test_file))
        obj.save()

        self.assertIsNone(getattr(obj.testfile.storage, 'result', None))

        self.assertFalse(
            path.isfile(path.join(self.remote_dir, obj.testfile.name)),
            "Remote file should not be transferred automatically.")

        result = obj.testfile.storage.transfer(obj.testfile.name)
        result.get()

        self.assertTrue(
            path.isfile(path.join(self.remote_dir, obj.testfile.name)),
            "Remote file is not available.")

    def test_remote_file_field(self):
        storage = QueuedStorage(
            local='django.core.files.storage.FileSystemStorage',
            remote='django.core.files.storage.FileSystemStorage',
            local_options=dict(location=self.local_dir),
            remote_options=dict(location=self.remote_dir),
            delayed=True)

        field = models.TestModel._meta.get_field('remote')
        field.storage = storage

        obj = models.TestModel(remote=File(self.test_file))
        obj.save()

        self.assertIsNone(getattr(obj.testfile.storage, 'result', None))

        result = obj.remote.transfer()
        self.assertTrue(result)
        self.assertTrue(path.isfile(path.join(self.remote_dir,
                                              obj.remote.name)))
