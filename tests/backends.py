import sys
import tempfile
from django.core.files.storage import FileSystemStorage, Storage


# Helper classes for easing the debugging

class LocalStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None):
        if location is None:
            location = tempfile.mkdtemp()
        sys.stdout.write('---> local ' + location + '\n')
        super(LocalStorage, self).__init__(location=location, base_url=base_url, file_permissions_mode=file_permissions_mode,
                                           directory_permissions_mode=directory_permissions_mode)


class RemoteStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None):
        if location is None:
            location = tempfile.mkdtemp()
        sys.stdout.write('---> remote ' + location + '\n')
        super(RemoteStorage, self).__init__(location=location, base_url=base_url, file_permissions_mode=file_permissions_mode,
                                            directory_permissions_mode=directory_permissions_mode)
