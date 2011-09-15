import codecs
from os import path
from setuptools import setup, find_packages

read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

setup(
    name='django-queued-storage',
    version=":versiontools:queued_storage:",
    description='Provides a proxy for django file storage, that allows you '
                'to upload files locally and eventually serve them remotely',
    long_description=read(path.join(path.dirname(__file__), 'README.rst')),
    author='Sean Brant, Josh VanderLinden',
    author_email='codekoala@gmail.com',
    maintainer='Jannis Leidel',
    maintainer_email='jannis@leidel.info',
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
