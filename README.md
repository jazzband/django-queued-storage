# django-queued-storage

This storage backend enables having a local and a remote storage backend. It 
will save any file locally and queue a task to transfer it somewhere else.

If the file is accessed before it's transferred, the local copy is returned.

The default tasks use [Celery](http://celeryproject.org/) for queing transfer
tasks but is agnostic about your choice.

## Installation

	pip install django-queued-storage

## Configuration

* Follow the configuration instructions for [django-celery](https://github.com/ask/django-celery)
* Set up a [caching backend](https://docs.djangoproject.com/en/1.3/topics/cache/#setting-up-the-cache)
* Add `queued_storage` to your `INSTALLED_APPS` tuple

## Usage

The `QueuedRemoteStorage` can be used as a drop-in replacement wherever 
`django.core.file.storage.Storage` might otherwise be required. 

This example is using [django-storages](http://code.welldev.org/django-storages/)
for the remote backend:

	from django.db import models
	from queued_storage.storage import QueuedRemoteStorage
	
	class MyModel(models.Model):
		image = ImageField(storage = QueuedRemoteStorage(
			local = 'django.core.files.storage.FileSystemStorage',
			remote = 'storages.backends.s3boto.S3BotoStorage'))


## Backends

* `queued_storage.backend.QueuedRemoteStorage`:  
  Base class for queued storages. You can use this to specify your own backends.

* `queued_storage.backend.DoubleFilesystemStorage`:  
  Used for testing, but can be handy if you want uploaded files to be stored in
  two places. Example:

		image = ImageField(
			storage = DoubleFilesystemStorage(
				local_kwargs = {'location': '/backup'},
				remote_kwargs = {'location': settings.MEDIA_ROOT}))
  

* `queued_storage.backend.S3Storage`:  
  Shortcut for the above example.

		image = ImageField(storage = S3Storage())


* `queued_storage.backend.DelayedStorage`:  
  This backend does *not* transfer files to the remote location automatically.

		image = ImageField(storage = DelayedStorage(
			'django.core.files.storage.FileSystemStorage',
			'storages.backends.s3boto.S3BotoStorage'))

		>>> m = MyModel(image = File(open('image.png')))
		>>> # Save locally:
		>>> m.save() 
		>>> # Transfer to remote location:
		>>> m.file.storage.transfer(m.file.name) 
  
  Useful if you want to do preprocessing

## Fields

* `queued_storage.backend.RemoteFileField`:  
  Tiny wrapper around any `QueuedRemoteStorage`, provides a convenient method
  to transfer files. The above `DelayedStorage` example would look like this:

    	image = RemoteFileField(storage = DelayedStorage(
			'django.core.files.storage.FileSystemStorage',
			'storages.backends.s3boto.S3BotoStorage'))
		
		>>> m = MyModel(image = File(open('image.png')))
		>>> # Save locally:
		>>> m.save() 
		>>> # Transfer to remote location:
		>>> m.file.transfer()

## Tasks

* `queued_storage.backend.Transfer`:  
  The default task. Transfers to a remote location. The actual transfer is
  implemented in the remote backend.

* `queued_storage.backend.TransferAndDelete`:  
  Once the file was transferred, the local copy is deleted.

To create new tasks, do something like this:

	from celery.registry import tasks
	from queued_storage.backend import Transfer

	class TransferAndDelete(Transfer):
	    def transfer(self, name, local, remote, **kwargs):
	        result = super(TransferAndDelete, self).transfer(name, local, remote, **kwargs)

	        if result:
	            local.delete(name)
	        
	        return result

	tasks.register(TransferAndDelete)

The result is `True` if the transfer was successful, else `False` and the task 
is retried.

In case you don't want to use Celery, have a look [here](https://github.com/flashingpumpkin/django-queued-storage/blob/master/queued_storage/tests/__init__.py#L80).

To use a different task, pass it into the backend:

	image = models.ImageField(storage = S3Storage(task = TransferAndDelete))

## Settings

* `QUEUED_STORAGE_CACHE_KEY`:  
  Use a different key for caching.

* `QUEUED_STORAGE_RETRIES`:  
  How many retries should be attempted before aborting.

* `QUEUED_STORAGE_RETRY_DELAY`:  
  The delay between retries.
  

# RELEASE NOTES

v0.3 - *BACKWARDS INCOMPATIBLE*

* Added tests
* Added `S3Storage` and `DelayedStorage`
* Added `TransferAndDelete` task
* Classes renamed to be consistent