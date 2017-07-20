from queued_storage.tasks import Transfer
from queued_storage.utils import import_attribute

from .models import TestModel


def test_task(name, cache_key,
              local_path, remote_path,
              local_options, remote_options):
    local = import_attribute(local_path)(**local_options)
    remote = import_attribute(remote_path)(**remote_options)
    remote.save(name, local.open(name))


def delay(*args, **kwargs):
    test_task(*args, **kwargs)

test_task.delay = delay


class NoneReturningTask(Transfer):
    def transfer(self, *args, **kwargs):
        return None


class RetryingTask(Transfer):
    def transfer(self, *args, **kwargs):
        if TestModel.retried:
            return True
        else:
            TestModel.retried = True
            return False
