from django.db.models.fields.files import FileField, FieldFile


class QueuedFieldFile(FieldFile):
    """
    A custom :class:`~django.db.models.fields.files.FieldFile` which has an
    additional method to transfer the file to the remote storage using the
    backend's ``transfer`` method.
    """
    def transfer(self):
        """
        Transfers the file using the storage backend.
        """
        return self.storage.transfer(self.name)


class QueuedFileField(FileField):
    """
    Field to be used together with
    :class:`~queued_storage.backends.QueuedStorage` instances or instances
    of subclasses.

    Tiny wrapper around :class:`~django:django.db.models.FileField`,
    which provides a convenient method to transfer files, using the
    :meth:`~queued_storage.fields.QueuedFieldFile.transfer` method, e.g.:

    .. code-block:: python

        from queued_storage.backends import QueuedS3BotoStorage
        from queued_storage.fields import QueuedFileField

        class MyModel(models.Model):
            image = QueuedFileField(storage=QueuedS3BotoStorage(delayed=True))

        my_obj = MyModel(image=File(open('image.png')))
        # Save locally:
        my_obj.save()
        # Transfer to remote location:
        my_obj.image.transfer()
    """
    attr_class = QueuedFieldFile
