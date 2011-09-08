"""
For simplicity and to avoid requiring a paid-for account on some cloud
storage system testing is conducted against two local storage backends. Since
the QueuedRemoteStorage backend is truly agnostic about the local and remote
storage systems, this should work as transparently as using one (or even two!)
remote storage systems.
"""
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, Storage
from django.core.management import call_command
from django.db import models
from django.utils.unittest.case import TestCase
from multiprocessing.process import Process
from queued_storage import backend
from queued_storage.backend import QueuedRemoteStorage
import os
import shutil
import tempfile
import time

class DoubleFilesystemStorage(QueuedRemoteStorage):
    def __init__(self, **kwargs):
        super(DoubleFilesystemStorage, self).__init__(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            **kwargs)

class TestModel(models.Model):
    file = models.FileField(upload_to='test/')
        

class BasicTest(TestCase):
    """
    Common setUp and tearDown methods for storage testing. "Stuff" is stored in
    a temporary directory and cleaned up afterwards.
    """

    def setUp(self):
        settings.CELERY_ALWAYS_EAGER = True
        self.local_dir = tempfile.mkdtemp()
        self.remote_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.local_dir)
        shutil.rmtree(self.remote_dir)


class StorageTests(BasicTest):
    def test_storage_init(self):
        """ Make sure that creating a QueuedRemoteStorage object works """
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            )
        self.assertTrue(isinstance(storage, QueuedRemoteStorage))
        
        self.assertEqual(FileSystemStorage, storage.local.__class__)
        self.assertEqual(FileSystemStorage, storage.remote.__class__)

    def test_storage_methods(self):
        """ Make sure that QueuedRemoteStorage implements all the methods """
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
        )
        
        file_storage = Storage()
        
        for attr in dir(file_storage):
            method = getattr(file_storage, attr)
            
            if not callable(method): 
                continue
            
            method = getattr(storage, attr, False)
            self.assertTrue(callable(method),
                "QueuedRemoteStorage has no method `%s`" % attr)
            
    def test_storage_simple_save(self):
        """ Make sure that saving to remote locations actually works """
        
        def task(name, local_class, remote_class, cache_key,
            local_args, local_kwargs, remote_args, remote_kwargs):
            local = local_class(*local_args, **local_kwargs)
            remote = remote_class(*remote_args, **remote_kwargs)

            remote.save(name, local.open(name))
            
            self.assertTrue(isinstance(local, FileSystemStorage))
            self.assertTrue(isinstance(remote, FileSystemStorage))
            
            remote.save(name, local.open(name))
        def delay(*args, **kwargs):
            task(*args, **kwargs)
        task.delay = delay

        
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
            task=task
        )
        field = TestModel._meta.get_field('file')
        field.storage = storage
        
        obj = TestModel(file=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()

        self.assertTrue(os.path.isfile(os.path.join(self.local_dir, obj.file.name)))
        self.assertTrue(os.path.isfile(os.path.join(self.remote_dir, obj.file.name)))
       
    def test_storage_celery_save(self):
        """ Make sure it actually works when using Celery as a task queue """
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
        )
        field = TestModel._meta.get_field('file')
        field.storage = storage
        
        obj = TestModel(file=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()

        obj.file.storage.result.get()

        self.assertTrue(os.path.isfile(os.path.join(self.local_dir, obj.file.name)))
        self.assertTrue(
            os.path.isfile(os.path.join(self.remote_dir, obj.file.name)),
            "Remote file is not available.")
        
        

