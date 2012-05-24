"""
django-queued-storage ships with a signal fired after a file was transfered
by the Transfer task. It provides the name of the file, the local and the
remote storage backend instances as arguments to connected signal callbacks.

Imagine you'd want to post-process the file that has been transfered from
the local to the remote storage, e.g. add it to a log model to always know
what exactly happened. All you'd have to do is to connect a callback to
the ``file_transferred`` signal::

    from django.dispatch import receiver
    from django.utils.timezone import now

    from queued_storage.signals import file_transferred

    from mysite.transferlog.models import TransferLogEntry


    @receiver(file_transferred)
    def log_file_transferred(sender, name, local, remote, **kwargs):
        remote_url = remote.url(name)
        TransferLogEntry.objects.create(name=name, remote_url=remote_url, transfer_date=now())

    # Alternatively, you can also use the signal's connect method to connect:
    file_transferred.connect(log_file_transferred)

Note that this signal does **NOT** have access to the calling Model or even
the FileField instance that it relates to, only the name of the file.
As a result, this signal is somewhat limited and may only be of use if you
have a very specific usage of django-queued-storage.
"""
from django.dispatch import Signal

file_transferred = Signal(providing_args=["name", "local", "remote"])
