from django.db import models

from queued_storage.fields import QueuedFileField

retried = False


class TestModel(models.Model):
    file = models.FileField(upload_to='test', null=True)
    remote = QueuedFileField(upload_to='test', null=True)
