from setuptools import setup, find_packages

setup(
    name='django-queued-storage',
    version='0.1',
    description='Provides a proxy for django file storage, that allows you to upload files locally and eventually serve them remotely',
    author='Sean Brant',
    author_email='brant.sean@gmail.com',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
)
