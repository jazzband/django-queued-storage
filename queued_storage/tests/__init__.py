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
from django.db import models
from django.utils.unittest.case import TestCase
from queued_storage.backend import QueuedRemoteStorage, DoubleFilesystemStorage, \
    S3Storage, DelayedStorage
from queued_storage.fields import RemoteFileField
from queued_storage.tasks import TransferAndDelete, Transfer
import os
import shutil
import tempfile

class TestModel(models.Model):
    file = models.FileField(upload_to='test/', null=True)
    remote = RemoteFileField(upload_to='test/', null=True)
        

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

        storage = DoubleFilesystemStorage(
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

    def test_transfer_and_delete(self):
        """ Make sure the TransferAndDelete task does what it says """
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
            task=TransferAndDelete
        )
        
        field = TestModel._meta.get_field('file')
        field.storage = storage
        
        obj = TestModel(file=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()

        obj.file.storage.result.get()
        
        self.assertFalse(
            os.path.isfile(os.path.join(self.local_dir, obj.file.name)),
            "Local file is still available")
        self.assertTrue(
            os.path.isfile(os.path.join(self.remote_dir, obj.file.name)),
            "Remote file is not available.")

    def test_transfer_returns_boolean(self):
        """ 
        Make sure an exception is thrown when the transfer task does not return
        a boolean. We don't want to confuse Celery. 
        """
        
        class NoneReturningTask(Transfer):
            def transfer(self, *args, **kwargs):
                return None
        
        storage = QueuedRemoteStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
            task=NoneReturningTask
        )
        
        field = TestModel._meta.get_field('file')
        field.storage = storage
        
        obj = TestModel(file=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()
        
        self.assertRaises(ValueError, obj.file.storage.result.get, propagate=True)
        
    def test_s3_storage(self):
        """ Make sure that initing the class works """
        self.assertTrue(isinstance(S3Storage(), S3Storage))
    
    def test_delayed_storage(self):
        storage = DelayedStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
        )
        
        field = TestModel._meta.get_field('file')
        field.storage = storage
        
        obj = TestModel(file=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()

        self.assertIsNone(getattr(obj.file.storage, 'result', None))
        
        self.assertFalse(
            os.path.isfile(os.path.join(self.remote_dir, obj.file.name)),
            "Remote file should not be transferred automatically.")

        result = obj.file.storage.transfer(obj.file.name)
        result.get()
        
        self.assertTrue(
            os.path.isfile(os.path.join(self.remote_dir, obj.file.name)),
            "Remote file is not available.")

    def test_remote_file_field(self):
        storage = DelayedStorage(
            'django.core.files.storage.FileSystemStorage',
            'django.core.files.storage.FileSystemStorage',
            local_kwargs={'location': self.local_dir},
            remote_kwargs={'location': self.remote_dir},
        )
        
        field = TestModel._meta.get_field('remote')
        field.storage = storage
        
        obj = TestModel(remote=File(open('%s/test.png' % os.path.dirname(__file__))))
        obj.save()

        self.assertIsNone(getattr(obj.file.storage, 'result', None))
        
        result = obj.remote.transfer()
        
        self.assertTrue(os.path.isfile(os.path.join(self.remote_dir, obj.remote.name)))
