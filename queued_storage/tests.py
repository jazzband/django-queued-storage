"""
For simplicity — and to avoid requiring a paid-for account on some cloud
storage system — testing is conducted against two local storage backends. Since
the QueuedRemoteStorage backend is truly agnostic about the local and remote
storage systems, this should work as transparently as using one (or even two!)
remote storage systems.
"""

import shutil
import tempfile

from django.tests import TestCase

from queued_storage import backend


class BasicTest(TestCase):
    """
    Common setUp and tearDown methods for storage testing. "Stuff" is stored in
    a temporary directory and cleaned up afterwards.
    """

    def setUp(self):
        self.local_dir = tempfile.mkdtemp()
        self.remote_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.local_dir)
        shutil.rmtree(self.remote_dir)


class StorageTests(BasicTest):
    def test_storage_saves_locally_and_remotely(self):
        klass = "django.core.files.storage.FileSystemStorage"
        storage = backend.QueuedRemoteStorage(local=klass, remote=klass,
                local_kwargs={"location": self.local_dir},
                remote_kwargs={"location": self.remote_dir})

    # TODO:
    #   - simple saving works
    #   - save without running celery task still has file available locally.
    #   - save clearing cache key checks if file is available remotely and uses
    #   that if possible.


# class FieldTests(BasicTest):
    # TODO: Test the storage as part of a field class.

