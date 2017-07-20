from queued_storage.tasks import Transfer

from .models import TestModel


class NoneReturningTransferTask(Transfer):
    def transfer(self, *args, **kwargs):
        return None


class RetryingTransferTask(Transfer):
    def transfer(self, *args, **kwargs):
        if TestModel.retried:
            return True
        else:
            TestModel.retried = True
            return False
