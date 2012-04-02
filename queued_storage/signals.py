"""
Note that this signal does NOT have access to the calling Model or even 
the FileField instance that it relates to, only the path. As a result, 
this signal is somewhat limited and may only be of use if you have a 
very specific usage of django-queued-storage.
"""
import django.dispatch
queued_storage_file_transferred = django.dispatch.Signal(providing_args=["path",])
