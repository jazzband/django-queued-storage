from setuptools import setup, find_packages
import queued_storage

setup(
    name='django-queued-storage',
    version=queued_storage.__version__,
    description='Provides a proxy for django file storage, that allows you to upload files locally and eventually serve them remotely',
    author='Sean Brant, Josh VanderLinden',
    author_email='codekoala@gmail.com',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    include_package_data=True,
    install_requires=['django-celery>=2.3.3'],
    zip_safe=False,
)
