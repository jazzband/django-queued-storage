from setuptools import setup, find_packages

setup(
    name='django-queued-storage',
    description='Provides a proxy for django file storage, that allows you to upload files locally and eventually serve them remotely',
    long_description = open('README.rst').read(),
    version=":versiontools:queued_storage:",
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
    setup_requires = [
        'versiontools >= 1.8',
    ],
    include_package_data=True,
    install_requires=['django-celery>=2.3.3'],
    zip_safe=False,
)
