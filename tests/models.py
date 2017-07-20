from django.db import models

from queued_storage.fields import QueuedFileField


class TestModel(models.Model):
    normal_file = models.FileField(upload_to='test_normal', null=True)
    queued_file = QueuedFileField(upload_to='test_queued', null=True)
    retried = False

    @staticmethod
    def queued_file_field_use_storage(storage):
        "Small static method to inject storage of the queued_file field dynamically."
        TestModel._meta.get_field('queued_file').storage = storage
