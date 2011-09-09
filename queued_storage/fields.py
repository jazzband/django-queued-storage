from django.db.models.fields.files import FileField, FieldFile

class RemoteFieldFile(FieldFile):
    def transfer(self):
        return self.storage.transfer(self.name)
    
class RemoteFileField(FileField):
    """ Field to be used together with QueuedStorageBackend """
    attr_class = RemoteFieldFile
    
    
    
